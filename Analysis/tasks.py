import law
import luigi
import os
import shutil
import time
import yaml
from RunKit.sh_tools import sh_call
from RunKit.checkRootFile import checkRootFileSafe

from run_tools.law_customizations import Task, HTCondorWorkflow, copy_param, get_param_value
from AnaProd.tasks import AnaTupleTask, DataMergeTask

class HistProducerFileTask(Task, HTCondorWorkflow, law.LocalWorkflow):
    max_runtime = copy_param(HTCondorWorkflow.max_runtime, 10.0)
    n_cpus = copy_param(HTCondorWorkflow.n_cpus, 1)

    def workflow_requires(self):
        return { "anaTuple" : AnaTupleTask.req(self, branches=())}

    def requires(self):
        sample_name, prod_br = self.branch_data
        if sample_name =='data':
            return [ DataMergeTask.req(self,max_runtime=DataMergeTask.max_runtime._default, branches=())]
        return [ AnaTupleTask.req(self, branch=prod_br, max_runtime=AnaTupleTask.max_runtime._default, branches=())]

    def create_branch_map(self):
        n = 0
        branches = {}
        anaProd_branch_map = AnaTupleTask.req(self, branch=-1, branches=()).create_branch_map()
        sample_id_data = 0
        for prod_br, (sample_id, sample_name, sample_type, input_file) in anaProd_branch_map.items():
            if sample_type =='data' or 'QCD' in sample_name:
                continue
            branches[n] = (sample_name, prod_br)#, anaProd_output)
            n+=1
        branches[n+1] = ('data', 0)#, dataMerge_output)
        return branches

    def output(self):
        sample_name, prod_br = self.branch_data
        anaProd_output = AnaTupleTask.req(self, branch=prod_br).output().path
        dataMerge_output = DataMergeTask.req(self).output().path
        input_file = anaProd_output if sample_name != 'data' else dataMerge_output
        inFile_idx_list = input_file.split('/')[-1].split('.')[0].split('_')
        inFile_idx = f'_{inFile_idx_list[1]}' if len(inFile_idx_list)>1 else ''
        if not os.path.isdir(self.central_Histograms_path()):
            os.makedirs(self.central_Histograms_path())
        hist_config = os.path.join(self.ana_path(), 'config', 'plot','histograms.yaml')
        with open(hist_config, 'r') as f:
            hist_cfg_dict = yaml.safe_load(f)
        vars_to_plot = list(hist_cfg_dict.keys())
        fileName = f'{sample_name}{inFile_idx}.root'
        local_files_target = []
        for var in vars_to_plot:
            outDir = os.path.join(self.central_Histograms_path(), sample_name, 'tmp', var)
            if not os.path.isdir(outDir):
                os.makedirs(outDir)
            outFile = os.path.join(outDir,fileName)
            local_files_target.append(law.LocalFileTarget(outFile))
        return local_files_target

    def run(self):
        sample_name, prod_br = self.branch_data
        anaProd_output = AnaTupleTask.req(self, branch=prod_br).output().path
        dataMerge_output = DataMergeTask.req(self).output().path
        input_file = anaProd_output if sample_name != 'data' else dataMerge_output
        inFile_idx_list = input_file.split('/')[-1].split('.')[0].split('_')
        inFile_idx = f'_{inFile_idx_list[1]}' if len(inFile_idx_list)>1 else ''
        hist_config = os.path.join(self.ana_path(), 'config', 'plot','histograms.yaml')
        unc_config = os.path.join(self.ana_path(), 'config', 'weight_definition.yaml')
        sample_config = self.sample_config
        HistProducerFile = os.path.join(self.ana_path(), 'Analysis', 'HistProducerFile.py')
        outDir = os.path.join(self.central_Histograms_path(), sample_name, 'tmp')
        HistProducerFile_cmd = ['python3', HistProducerFile,'--inFile', input_file, '--dataset', sample_name, '--outDir', outDir,
                            '--compute_unc_variations', 'True', '--compute_rel_weights', 'True',
                            '--uncConfig', unc_config, '--histConfig', hist_config,'--sampleConfig', sample_config]
        sh_call(HistProducerFile_cmd,verbose=1)


class HistProducerSampleTask(Task, HTCondorWorkflow, law.LocalWorkflow):
    max_runtime = copy_param(HTCondorWorkflow.max_runtime, 1.0)

    def workflow_requires(self):
        return { "histProducerFile" : HistProducerFileTask.req(self, branches=())}

    def requires(self):
        histProducerFile_map = HistProducerFileTask.req(self, branch=-1, branches=()).create_branch_map()
        sample_name = self.branch_data
        reqs = []
        for br_idx, (smpl_name, prod_br) in histProducerFile_map.items():
            if smpl_name == sample_name:
                reqs.append( HistProducerFileTask.req(self, branch=br_idx, max_runtime=HistProducerFileTask.max_runtime._default, branches=()))
        return reqs

    def create_branch_map(self):
        n = 0
        branches = {}
        already_considered_samples = []
        histProducerFile_map = HistProducerFileTask.req(self, branch=-1, branches=()).create_branch_map()
        for br_idx, (sample_name, prod_br) in histProducerFile_map.items():
            if sample_name in already_considered_samples:
                continue
            branches[n] = sample_name
            already_considered_samples.append(sample_name)
            n+=1
        return branches

    def output(self):
        sample_name = self.branch_data
        hist_config = os.path.join(self.ana_path(), 'config', 'plot','histograms.yaml')
        with open(hist_config, 'r') as f:
            hist_cfg_dict = yaml.safe_load(f)
        vars_to_plot = list(hist_cfg_dict.keys())
        fileName = f'{sample_name}.root'
        local_files_target = []
        for var in vars_to_plot:
            outDir = os.path.join(self.central_Histograms_path(), sample_name, var)
            if not os.path.isdir(outDir):
                os.makedirs(outDir)
            outFile = os.path.join(outDir,fileName)
            local_files_target.append(law.LocalFileTarget(outFile))
        return local_files_target

    def run(self):
        sample_name = self.branch_data
        histProducerFile_map = HistProducerFileTask.req(self, branch=-1, branches=()).create_branch_map()
        files_idx = []
        hist_config = os.path.join(self.ana_path(), 'config', 'plot','histograms.yaml')
        with open(hist_config, 'r') as f:
            hist_cfg_dict = yaml.safe_load(f)
        vars_to_plot = list(hist_cfg_dict.keys())
        hists_str = ','.join(var for var in vars_to_plot)
        file_ids_str = ''
        file_name_pattern = sample_name
        for br_idx, (smpl_name, prod_br) in histProducerFile_map.items():
            if smpl_name == sample_name:
                files_idx.append(br_idx)
        if(len(files_idx)>1):
            file_name_pattern +="_{id}"
            file_ids_str = f"{files_idx[0]}-{files_idx[-1]}"
        #HistProducerSample.py --histDir my/hist/dir --outDir my/out/dir --hists m_tautau,tau1_pt --file-name-pattern 'nano_{id}.root' --file-ids '0-100
        file_name_pattern += ".root"
        outFileName = f'{sample_name}.root'
        HistProducerSample = os.path.join(self.ana_path(), 'Analysis', 'HistProducerSample.py')
        outDir = os.path.join(self.central_Histograms_path(), sample_name)
        histDir = os.path.join(self.central_Histograms_path(), sample_name, 'tmp')
        HistProducerSample_cmd = ['python3', HistProducerSample,'--histDir', histDir, '--outDir', outDir, '--hists', hists_str,
                            '--file-name-pattern', file_name_pattern, '--outFileName', outFileName]
        if(len(files_idx)>1):
            HistProducerSample_cmd.extend(['--file-ids', file_ids_str])
        #sh_call(HistProducerSample_cmd,verbose=1)
        print(HistProducerSample_cmd)