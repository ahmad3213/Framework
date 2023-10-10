import os
import ROOT
from .CorrectionsCore import *
from Common.Utilities import WorkingPointsbTag
import yaml



class bTagCorrProducer:
    jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/{}/btagging.json.gz"
    bTagEff_JsonPath = "Corrections/data/BTV/{}/btagEff.root"
    initialized = False
    SFSources = ["btagSFbc_uncorrelated", "btagSFlight_uncorrelated","btagSFbc_correlated", "btagSFlight_correlated"]


    def __init__(self, period, loadEfficiency=True):
        jsonFile = bTagCorrProducer.jsonPath.format(period)
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],bTagCorrProducer.bTagEff_JsonPath.format(period))
        if not loadEfficiency:
            jsonFile_eff = ""
        if not bTagCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "btag.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::bTagCorrProvider::Initialize("{jsonFile}", "{jsonFile_eff}")')
            bTagCorrProducer.initialized = True

    def getWPValues(self):
        wp_values = {}
        for wp in WorkingPointsbTag:
            root_wp = getattr(ROOT.WorkingPointsbTag, wp.name)
            wp_values[wp] = ROOT.correction.bTagCorrProvider.getGlobal().getWPvalue(root_wp)
        return wp_values

    def getWPid(self, df):
        wp_values = self.getWPValues()
        df = df.Define("Jet_idbtagDeepFlavB", f"::correction::bTagCorrProvider::getGlobal().getWPBranch(Jet_btagDeepFlavB)")
        return df

    def getSF(self, df, return_variations=True, isCentral=True):
        sf_sources = bTagCorrProducer.SFSources if return_variations else []
        SF_branches = []
        for source in [ central ] + sf_sources:
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                if not isCentral and scale!= central: continue
                for wp in WorkingPointsbTag:
                    branch_name = f"weight_bTagSF_{wp.name}_{syst_name}"
                    branch_central = f"""weight_bTagSF_{wp.name}_{getSystName(central, central)}"""
                    df = df.Define(f"{branch_name}_double",
                                f''' ::correction::bTagCorrProvider::getGlobal().getSF(
                                Jet_p4, Jet_bCand, Jet_hadronFlavour, Jet_btagDeepFlavB, WorkingPointsbTag::{wp.name},
                            ::correction::bTagCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) ''')
                    if source != central:
                        df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                        branch_name += '_rel'
                    else:
                        df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                    SF_branches.append(f"{branch_name}")
        return df,SF_branches


