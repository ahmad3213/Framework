import os
indir = "/eos/user/m/muahmad/ANA_FOLDER/histograms/common/Run3_2022EE/merged/"
varnames = ["lep1_Muon_pfRelIso04_all", "lep2_Muon_pfRelIso04_all", "lep1_Electron_miniPFRelIso_all", "lep2_Electron_miniPFRelIso_all", "bjet1_btagPNetB", "bjet2_btagPNetB", "diLep_mass", "Lep1Jet1Jet2_mass", "Lep1Lep2Jet1Jet2_mass", "Njets", "bjet1_pt", "bjet2_pt", "HT", "dR_dilep", "dR_dibjet", "dR_dilep_dibjet", "dPhi_lep1_lep2", "dPhi_jet1_jet2", "dPhi_MET_dilep", "dPhi_MET_dibjet", "min_dR_lep0_jets", "min_dR_lep1_jets", "bb_mass", "bb_mass_PNetRegPtRawCorr", "bb_mass_PNetRegPtRawCorr_PNetRegPtRawCorrNeutrino", "PuppiMET_pt", "PuppiMET_phi"]
#varnames = ["lep1_pt"]
channellist = ["muMu"]
era = "Run3_2022EE"
plotpath = "/eos/user/m/muahmad/www_test/plots_9April_2022EE/"
plotpath = "plots_9April_2022EE/"
index_file_location = "/eos/user/m/muahmad/www_test/index.php"
categories = ["inclusive","boosted","baseline","res1b","res2b"]
regions = ["OS_Iso","SS_Iso","OS_AntiIso","SS_AntiIso","Zpeak_0b","Zpeak_1b","Zpeak_2b","ZVeto_0b","ZVeto_1b","ZVeto_2b","TTbar_CR"]
using_uncertainties = False #When we turn on Up/Down, the file storage changes due to renameHists.py

for var in varnames:
    for channel in channellist:
        for cat in categories:
            for reg in regions:
                filename = os.path.join(indir, var, f"{var}.root")
                print("Loading fname ", filename)
                plotdir = os.path.join(plotpath, f"{channel}_{cat}_{reg}")
                os.makedirs(plotdir, exist_ok=True)
                os.system(f"cp {index_file_location} {plotdir}")
                outname = os.path.join(plotdir, f"HHbbWW_{var}_{channel}_{cat}_{reg}_StackPlot.pdf")
                if not using_uncertainties:
                    os.system(f"python3 ../HistPlotter.py --inFile {filename} --bckgConfig ../../config/HH_bbWW/background_samples.yaml --globalConfig ../../config/HH_bbWW/global.yaml --outFile {outname} --var {var} --category {cat} --channel {channel} --uncSource Central --wantData --year {era} --wantQCD False --rebin False --analysis HH_bbWW --qcdregion {reg} --sigConfig ../../config/HH_bbWW/{era}/samples.yaml")
                else:
                    filename = os.path.join(indir, var, 'tmp', f"all_histograms_{var}_hadded.root")
                    os.system(f"python3 ../HistPlotter.py --inFile {filename} --bckgConfig ../../config/HH_bbWW/background_samples.yaml --globalConfig ../../config/HH_bbWW/global.yaml --outFile {outname} --var {var} --category {cat} --channel {channel} --uncSource Central --wantData --year {era} --wantQCD False --rebin False --analysis HH_bbWW --qcdregion {reg} --sigConfig ../../config/HH_bbWW/{era}/samples.yaml")
