set root E:/new/fpga_lock/v94
set evidence E:/new/fpga_lock/v94/v0.94/exp/l1-candidate-20260911
open_project [file join $root v0.94 project redpitaya.xpr]
set run [get_runs l1_candidate_impl_20260911]
launch_runs $run -to_step route_design -jobs 2 -dir [file join $evidence build]
wait_on_run $run
puts "RESUME_STATUS=[get_property STATUS $run]"
if {![string match "*Complete*" [get_property STATUS $run]]} { error "resume failed" }
open_run $run
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
  -file [file join $evidence current_timing_summary.rpt]
check_timing -verbose -file [file join $evidence current_check_timing.rpt]
report_route_status -file [file join $evidence current_route_status.rpt]
report_drc -file [file join $evidence current_drc.rpt]
report_cdc -file [file join $evidence current_cdc.rpt]
report_methodology -file [file join $evidence current_methodology.rpt]
report_utilization -hierarchical -file [file join $evidence current_utilization.rpt]
write_checkpoint -force [file join $evidence current_routed.dcp]
close_project
exit
