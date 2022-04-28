from staticfg import CFGBuilder

cfg = CFGBuilder().build_from_file('example.py', './VSCServer.py')
cfg.build_visual('exampleCFG','pdf')