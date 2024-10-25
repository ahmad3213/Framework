import ROOT
if __name__ == "__main__":
    sys.path.append(os.environ['ANALYSIS_PATH'])

from Analysis.HistHelper import *
from Common.Utilities import *


def createKeyFilterDict(global_cfg_dict):
    reg_dict = {}
    filter_str = ""
    channels_to_consider = global_cfg_dict['channels_to_consider']
    qcd_regions_to_consider = global_cfg_dict['QCDRegions']
    categories_to_consider = global_cfg_dict["categories"]
    #triggers = global_cfg_dict['hist_triggers']
    #mass_cut_limits = global_cfg_dict['mass_cut_limits']
    for ch in channels_to_consider:
        for reg in qcd_regions_to_consider:
            for cat in categories_to_consider:
                #print(ch, reg, cat, filter_str)
                #print()
                #filter_base = f" ({ch} && {triggers[ch]} && {reg} && {cat})"
                filter_base = f" ({ch} && {reg} && {cat})"
                filter_str = f"(" + filter_base
                #print(ch, reg, cat, filter_str)
                #print()
                #for mass_name,mass_limits in mass_cut_limits.items():
                #    filter_str+=f"&& ({mass_name} >= {mass_limits[0]})"
                #print(filter_str)
                #if cat != 'boosted' and cat!= 'baseline':
                #    filter_str += "&& (b1_pt>0 && b2_pt>0)"
                filter_str += ")"
                #print(filter_str)
                key = (ch, reg, cat)
                reg_dict[key] = filter_str
                #print(ch, reg, cat, filter_str)
                #print()

    return reg_dict

def ApplyBTagWeight(global_cfg_dict,cat,applyBtag=False):
    #This does not just apply btag, but it replaces the existing weight with a new weight! So dumb!!!
    btag_weight = "1"
    btagshape_weight = "1"
    if applyBtag:
        if global_cfg_dict['btag_wps'][cat]!='' : btag_weight = f"weight_bTagSF_{btag_wps[cat]}_Central"
    else:
        if cat !='btag_shape' and cat !='boosted': btagshape_weight = "weight_bTagShape_Central"
    return f'1.'
    #return f'{btag_weight}*{btagshape_weight}'


def GetWeight(channel, cat):
    weights_to_apply = ["weight_MC_Lumi_pu"]
    total_weight = '*'.join(weights_to_apply)
    return total_weight


def AddQCDInHistDict(var, all_histograms, channels, categories, uncName, all_samples_list, scales, unc_to_not_consider_boosted, wantNegativeContributions=False):
    return



class DataFrameBuilderForHistograms(DataFrameBuilderBase):

    def defineCategories(self):
        self.bTagWP = 0.43 #Temp for now, everything is a 'b jet'
        self.df = self.df.Define("nSelBtag", f"int(bjet1_btagPNetB >= {self.bTagWP}) + int(bjet2_btagPNetB >= {self.bTagWP})")

        #self.df = self.df.Define("nSelBtag", f"int(centralJet_btagPNetB >= {self.bTagWP}) + int(centralJet_btagPNetB >= {self.bTagWP})")
        #self.df = self.df.Define("boosted", "nSelectedFatJet > 0")
        self.df = self.df.Define("boosted", "SelectedFatJet_pt.size() > 0")
        self.df = self.df.Define("res1b", f"!boosted && nSelBtag == 1")
        self.df = self.df.Define("res2b", f"!boosted && nSelBtag == 2")
        self.df = self.df.Define("inclusive", f"!boosted")
        self.df = self.df.Define("baseline",f"return true;")

    def defineChannels(self):
        self.df = self.df.Define("channelId", f"(lep1_type*10) + lep2_type")
        for channel in self.config['channelSelection']:
            ch_value = self.config['channelDefinition'][channel]
            self.df = self.df.Define(f"{channel}", f"channelId=={ch_value}")

    def defineLeptonPreselection(self):
        # self.df = self.df.Define("lep1_tight", "(lep1_type == 1 && lep1_pt > 25) || (lep1_type == 2 && lep1_pt > 15)") #Dummy values, EleGt25 and MuGt15
        # self.df = self.df.Define("lep2_tight", "(lep2_type == 1 && lep2_pt > 25) || (lep2_type == 2 && lep2_pt > 15)") #Dummy values, EleGt25 and MuGt15

        # self.df = self.df.Define(f"lepton_preselection", "(lep1_tight)")
        # self.df = self.df.Filter(f"lepton_preselection")

        self.df = self.df.Define("passed_singleIsoMu", "HLT_singleIsoMu && ((lep1_type == 2 && lep1_HasMatching_singleIsoMu) || (lep2_type == 2 && lep2_lep1_HasMatching_singleIsoMu))")
        self.df = self.df.Filter(f"passed_singleIsoMu")

    def defineJetSelections(self):
        self.df = self.df.Define("jet1_isvalid", "centralJet_pt.size() > 0")
        self.df = self.df.Define("jet2_isvalid", "centralJet_pt.size() > 1")
        self.df = self.df.Define("fatjet_isvalid", "SelectedFatJet_pt.size() > 0")

        self.df = self.df.Define("bjet1_btagPNetB", "jet1_isvalid ? centralJet_btagPNetB[0] : -1.0")
        self.df = self.df.Define("bjet2_btagPNetB", "jet2_isvalid ? centralJet_btagPNetB[1] : -1.0")
        self.df = self.df.Define("bsubjet1_btagDeepB", "fatjet_isvalid ? SelectedFatJet_SubJet1_btagDeepB[0] : -1.0")
        self.df = self.df.Define("bsubjet2_btagDeepB", "fatjet_isvalid ? SelectedFatJet_SubJet2_btagDeepB[0] : -1.0")


    def defineQCDRegions(self):
        self.df = self.df.Define("OS", "(lep2_type < 1) || (lep1_charge*lep2_charge < 0)")
        self.df = self.df.Define("Iso", f"( (lep1_type == 1 && lep1_Electron_mvaIso_WP90) || (lep1_type == 2 && lep1_pfIsoId >=2) ) && (lep2_type < 1 || ( (lep2_type == 1 && lep2_Electron_mvaIso_WP90) || (lep2_type == 2 && lep2_pfIsoId >= 2) ))")
        self.df = self.df.Define("OS_Iso", f"OS && Iso") 



    def selectTrigger(self, trigger):
        self.df = self.df.Filter(trigger)

    def addCut (self, cut=""):
        if cut!="":
            self.df = self.df.Filter(cut)



    def defineTriggers(self):
        for ch in self.config['channelSelection']:
            for trg in self.config['triggers'][ch].split(' || '):
                if trg not in self.df.GetColumnNames():
                    print(f"{trg} not present in colNames")
                    self.df = self.df.Define(trg, "1")


        singleTau_th_dict = self.config['singleTau_th']
        #singleMu_th_dict = self.config['singleMu_th']
        #singleEle_th_dict = self.config['singleEle_th']
        for trg_name,trg_dict in self.config['application_regions'].items():
            for key in trg_dict.keys():
                region_name = trg_dict['region_name']
                region_cut = trg_dict['region_cut'].format(tau_th=singleTau_th_dict[self.period])
                if region_name not in self.df.GetColumnNames():
                    self.df = self.df.Define(region_name, region_cut)

    def __init__(self, df, config, period, **kwargs):
        super(DataFrameBuilderForHistograms, self).__init__(df, **kwargs)
        self.config = config
        self.period = period



def PrepareDfForHistograms(dfForHistograms):
    #dfForHistograms.df = defineAllP4(dfForHistograms.df)
    dfForHistograms.defineChannels()
    dfForHistograms.defineLeptonPreselection()
    dfForHistograms.defineJetSelections()
    dfForHistograms.defineQCDRegions()
    #dfForHistograms.defineBoostedVariables()
    dfForHistograms.defineCategories()
    #dfForHistograms.defineTriggers()
    #dfForHistograms.redefineWeights()
    #dfForHistograms.df = createInvMass(dfForHistograms.df)
    return dfForHistograms
