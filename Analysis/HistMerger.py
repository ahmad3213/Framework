import ROOT
import sys
import os
import math
import shutil
import time
from RunKit.run_tools import ps_call
if __name__ == "__main__":
    sys.path.append(os.environ['ANALYSIS_PATH'])

import Common.Utilities as Utilities
from Analysis.HistHelper import *
from Analysis.QCD_estimation import *

import importlib
which_ana = ((args.globalConfig['analysis_config_area']).lower()
analysis = importlib.import_module(f'Analysis.{which_ana}')

def checkFile(inFileRoot, channels, qcdRegions, categories, var):
    keys_channels = [str(key.GetName()) for key in inFileRoot.GetListOfKeys()]
    # if not (Utilities.checkLists(keys_channel, channels)):
    #     print("check list not worked for channels")
    for channel in channels:
        if channel not in keys_channels:
            return False
    for channel in channels:
        dir_0 = inFileRoot.Get(channel)
        keys_qcdRegions = [str(key.GetName()) for key in dir_0.GetListOfKeys()]
        if not all(element in keys_qcdRegions for element in QCDregions):
            print("check list not worked for QCDregions")
            return False
        for qcdRegion in QCDregions:
            dir_1 = dir_0.Get(qcdRegion)
            keys_categories = [str(key.GetName()) for key in dir_1.GetListOfKeys()]
            if not all(element in keys_categories for element in categories):
                    print("check list not worked for categories")
                    return False
            for cat in categories:
                dir_2 = dir_1.Get(cat)
                keys_histograms = [str(key.GetName()) for key in dir_2.GetListOfKeys()]
                if not keys_histograms: return False
    return True



def getHistDict(var, all_histograms, inFileRoot,channels, QCDregions, all_categories, uncSource,sample_name,sample_type, sample_types_to_merge):
    name_to_use = sample_name
    if sample_type in sample_types_to_merge:
        name_to_use = sample_type
    if name_to_use not in all_histograms.keys():
        all_histograms[name_to_use] = {}
        # print(f"name to use is {name_to_use}")
        # print(all_histograms.keys())
    for channel in channels:
        dir_0 = inFileRoot.Get(channel)
        #print(dir_0.GetListOfKeys())
        for qcdRegion in QCDregions:
            dir_1 = dir_0.Get(qcdRegion)
            #print(dir_1.GetListOfKeys())
            for cat in all_categories:
                # print(cat, var)
                key_total = ((channel, qcdRegion, cat), (uncSource, 'Central'))
                # print(key_total)
                dir_2 = dir_1.Get(cat)
                if uncSource == 'Central':
                    key_to_use = sample_name
                    obj=dir_2.Get(key_to_use)
                    obj.SetDirectory(0)
                    if not obj.IsA().InheritsFrom(ROOT.TH1.Class()): continue
                    if key_total not in all_histograms[name_to_use].keys():
                        all_histograms[name_to_use][key_total] = []
                    all_histograms[name_to_use][key_total].append(obj)
                elif uncSource == 'QCDScale':
                    key_to_use = sample_name
                    obj=dir_2.Get(key_to_use)
                    obj.SetDirectory(0)
                    for scale in ['Up','Down']:
                        key_total_QCD = ((channel, qcdRegion, cat), ('QCDScale', scale))
                        if key_total_QCD not in all_histograms[name_to_use].keys():
                            all_histograms[name_to_use][key_total_QCD] = []
                        all_histograms[name_to_use][key_total_QCD].append(obj)
                else:
                    key_to_use = sample_name + '_' + uncSource
                    for scale in ['Up', 'Down']:
                        key_final = key_to_use+scale
                        # print(key_final)
                        if sample_name=='data':
                            key_final = 'data'
                        obj=dir_2.Get(key_final)
                        obj.SetDirectory(0)
                        if not obj.IsA().InheritsFrom(ROOT.TH1.Class()): continue
                        key_total = ((channel, qcdRegion, cat), (uncSource, scale))
                        if key_total not in all_histograms[name_to_use].keys():
                            all_histograms[name_to_use][key_total] = []
                        all_histograms[name_to_use][key_total].append(obj)
    # print(all_histograms)


def MergeHistogramsPerType(all_histograms):
    for sample_type in all_histograms.keys():
        if sample_type == 'data': print(f"DURING MERGE HISTOGRAMS, sample_type is {sample_type}")
        for key_name,histlist in all_histograms[sample_type].items():
            final_hist =  histlist[0]
            objsToMerge = ROOT.TList()
            for hist in histlist[1:]:
                objsToMerge.Add(hist)
            final_hist.Merge(objsToMerge)
            all_histograms[sample_type][key_name] = final_hist
            #if len(histlist)!=1:
                #print(f"for {sample_type} the lenght of histlist is {len(histlist)}")



def GetBTagWeightDict(var,all_histograms, categories, boosted_categories, boosted_variables):
    all_histograms_1D = {}
    for sample_type in all_histograms.keys():
        #print(sample_type)
        all_histograms_1D[sample_type] = {}
        for key_name,histogram in all_histograms[sample_type].items():
            (key_1, key_2) = key_name

            if var not in boosted_variables:
                ch, reg, cat = key_1
                uncName,scale = key_2
                key_tuple_num = ((ch, reg, 'btag_shape'), key_2)
                key_tuple_den = ((ch, reg, 'inclusive'), key_2)
                ratio_num_hist = all_histograms[sample_type][key_tuple_num] if key_tuple_num in all_histograms[sample_type].keys() else None
                ratio_den_hist = all_histograms[sample_type][key_tuple_den] if key_tuple_den in all_histograms[sample_type].keys() else None
                num = ratio_num_hist.Integral(0,ratio_num_hist.GetNbinsX()+1)
                den = ratio_den_hist.Integral(0,ratio_den_hist.GetNbinsX()+1)
                ratio = 0.
                if ratio_den_hist.Integral(0,ratio_den_hist.GetNbinsX()+1) != 0 :
                    ratio = ratio_num_hist.Integral(0,ratio_num_hist.GetNbinsX()+1)/ratio_den_hist.Integral(0,ratio_den_hist.GetNbinsX()+1)
                if cat in boosted_categories or cat.startswith("inclusive") or cat.startswith("btag_shape") or cat.startswith("baseline") :
                    ratio = 1
                #print(f"for cat {cat} setting ratio is {ratio}")
                histogram.Scale(ratio)
            else:
                print(f"for var {var} no ratio is considered and the histogram is directly saved")

            all_histograms_1D[sample_type][key_name] = histogram
            # print(sample_type, key_name, histogram.Integral(0, histogram.GetNbinsX()+1))
    return all_histograms_1D



if __name__ == "__main__":
    import argparse
    import yaml
    parser = argparse.ArgumentParser()
    parser.add_argument('inputFile', nargs='+', type=str)
    #parser.add_argument('datasetFile', nargs='+', type=str)
    parser.add_argument('--outFile', required=True, type=str)
    parser.add_argument('--year', required=True, type=str)
    parser.add_argument('--datasetFile', required=True, type=str)
    parser.add_argument('--var', required=True, type=str)
    parser.add_argument('--sampleConfig', required=True, type=str)
    parser.add_argument('--globalConfig', required=True, type=str)
    parser.add_argument('--uncConfig', required=True, type=str)
    parser.add_argument('--uncSource', required=False, type=str,default='Central')
    parser.add_argument('--region', required=False, type=str,default='SR')
    parser.add_argument('--channels', required=False, type=str,default='eTau,muTau,tauTau')

    args = parser.parse_args()
    startTime = time.time()
    with open(args.uncConfig, 'r') as f:
        unc_cfg_dict = yaml.safe_load(f)
    with open(args.sampleConfig, 'r') as f:
        sample_cfg_dict = yaml.safe_load(f)
    with open(args.globalConfig, 'r') as f:
        global_cfg_dict = yaml.safe_load(f)

    all_samples_list = args.datasetFile.split(',')
    all_samples_types = {}
    all_samples_names = {}
    uncNameTypes = GetUncNameTypes(unc_cfg_dict)

    if args.uncSource != 'Central' and args.uncSource not in uncNameTypes:
        print("unknown unc source {args.uncSource}")

    categories = list(global_cfg_dict['categories'])
    boosted_categories = list(global_cfg_dict['boosted_categories'])
    QCDregions = list(global_cfg_dict['QCDRegions'])
    global_cfg_dict['channels_to_consider']=args.channels.split(',')

    channels = global_cfg_dict['channels_to_consider']
    # print(channels)

    signals = list(global_cfg_dict['signal_types'])
    unc_to_not_consider_boosted = list(global_cfg_dict['unc_to_not_consider_boosted'])
    boosted_variables = list(global_cfg_dict['var_only_boosted'])

    all_categories = categories + boosted_categories
    if args.var in boosted_variables:
        all_categories = boosted_categories

    if (args.var.startswith('b1') or args.var.startswith('b2')):
        all_categories = categories

    sample_types_to_merge = list(global_cfg_dict['sample_types_to_merge'])
    scales = list(global_cfg_dict['scales'])
    files_separated = {}
    all_histograms ={}
    all_infiles = [ fileName for fileName in args.inputFile ]
    if len(all_infiles) != len(all_samples_list):
        raise RuntimeError(f"all_infiles have len {len(all_infiles)} and all_samples_list have len {len(all_samples_list)}")
    ignore_samples = []
    for (inFileName, sample_name) in zip(all_infiles, all_samples_list):
        if not os.path.exists(inFileName):
            print(f"{inFileName} does not exist")
            continue
            #raise RuntimeError(f"{inFileName} removed")
        #print(sample_name)

        #Sometimes we do not want to stack all samples (signal)
        if 'samples_to_skip_hist' in global_cfg_dict.keys():
            #Add this key check to avoid breaking bbtautau
            if sample_name in global_cfg_dict['samples_to_skip_hist']:
                continue

        inFileRoot = ROOT.TFile.Open(inFileName, "READ")
        if inFileRoot.IsZombie():
            inFileRoot.Close()
            os.remove(inFileName)
            ignore_samples.append(sample_name)
            raise RuntimeError(f"{inFileName} is Zombie")
        if  not checkFile(inFileRoot, channels, QCDregions, all_categories,args.var):
            print(f"{sample_name} has void file")
            ignore_samples.append(sample_name)
            inFileRoot.Close()
            continue
        sample_type= 'data' if sample_name == 'data' else sample_cfg_dict[sample_name]['sampleType']
        getHistDict(args.var,all_histograms, inFileRoot,channels, QCDregions, all_categories, args.uncSource,sample_name,sample_type,sample_types_to_merge)
        # print(all_histograms.keys())
        inFileRoot.Close()
        if sample_name == 'data':
            all_samples_types['data'] = ['data']
        else:
            sample_key = sample_type if sample_type in sample_types_to_merge else sample_name
            if sample_name not in ignore_samples:
                if sample_key not in all_samples_types.keys(): all_samples_types[sample_key] = []
                all_samples_types[sample_key].append(sample_name)

    # for key in all_histograms.keys():
    #     print(key, len(all_histograms[key]))
    # for key in all_samples_types.keys():
    #     print(key, all_samples_types[key])

    MergeHistogramsPerType(all_histograms)
    all_histograms_1D=GetBTagWeightDict(args.var,all_histograms, categories, boosted_categories, boosted_variables)
    # print(all_histograms_1D)

    # for key in all_histograms_1D.keys():
    #     print(key)

    #     for subdict,hito in all_histograms_1D[key].items():
    #         print(subdict)
    #         histo = hito.Clone()
    #         # hito = all_histograms_1D[key]
    #         print(f"integral is {histo.Integral(0,histo.GetNbinsX())}")

    fixNegativeContributions = False
    # if args.var != 'kinFit_m':
        # fixNegativeContributions=True
    # print(args.var, all_histograms_1D, channels, all_categories, args.uncSource, all_samples_types.keys(), scales)
    error_on_qcdnorm,error_on_qcdnorm_varied = AddQCDInHistDict(args.var, all_histograms_1D, channels, all_categories, args.uncSource, all_samples_types.keys(), scales, wantNegativeContributions=False)

    outFile = ROOT.TFile(args.outFile, "RECREATE")


    for sample_type in all_histograms_1D.keys():

        for key in all_histograms_1D[sample_type]:
            (channel, qcdRegion, cat), (uncNameType, uncScale) = key
            #if qcdRegion != 'OS_Iso': continue
            dirStruct = (channel,qcdRegion, cat)
            dir_name = '/'.join(dirStruct)
            dir_ptr = Utilities.mkdir(outFile,dir_name)
            hist = all_histograms_1D[sample_type][key]
            #print(sample_type, key, hist.GetEntries())
            hist_name =  sample_type
            if uncNameType!=args.uncSource: continue
            if uncNameType != 'Central':
                if sample_type == 'data' : continue
                if uncScale == 'Central': continue
                hist_name+=f"_{uncNameType}_{uncScale}"
            else:
                if uncScale!='Central':continue
            hist.SetTitle(hist_name)
            hist.SetName(hist_name)
            dir_ptr.WriteTObject(hist, hist_name, "Overwrite")
    outFile.Close()
    executionTime = (time.time() - startTime)

    print('Execution time in seconds: ' + str(executionTime))
