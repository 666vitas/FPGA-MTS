help open_project
help create_run
open_project -read_only E:/new/fpga_lock/v94/v0.94/project/redpitaya.xpr
puts "SYNTH_FLOW=[get_property FLOW [get_runs synth_1]]"
puts "SYNTH_STRATEGY=[get_property STRATEGY [get_runs synth_1]]"
puts "IMPL_FLOW=[get_property FLOW [get_runs impl_1]]"
puts "IMPL_STRATEGY=[get_property STRATEGY [get_runs impl_1]]"
report_property [get_runs synth_1]
report_property [get_runs impl_1]
close_project
exit
