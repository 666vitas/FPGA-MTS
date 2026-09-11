set root E:/new/fpga_lock/v94
set evidence E:/new/fpga_lock/v94/v0.94/exp/l1-candidate-20260911
set build_dir [file join $evidence build_explore]
set synth_name l1_candidate_synth_explore_20260911
set impl_name l1_candidate_impl_explore_20260911
open_project [file join $root v0.94 project redpitaya.xpr]
if {[version -short] ne "2020.1"} { error "Vivado 2020.1 required" }
proc clone_steps {from to} {
    foreach prop [list_property [get_runs $from]] {
        if {[regexp {^STEPS\..*\.(ARGS\.|IS_ENABLED$|TCL\.)} $prop]} {
            set_property $prop [get_property $prop [get_runs $from]] [get_runs $to]
        }
    }
}
set identity [open [file join $evidence candidate_build_identity.txt] w]
puts $identity "Vivado=[version -short]"
puts $identity "XPR=[file join $root v0.94 project redpitaya.xpr]"
puts $identity "HEAD=[exec git -C $root rev-parse HEAD]"
puts $identity "Top=[get_property TOP [get_filesets sources_1]]"
puts $identity "Part=[get_property PART [current_project]]"
puts $identity "ENABLE_DAISY=0; DNA clock=adc_clk/16; PHYS_OPT=disabled after Vivado 2020.1 crash; ROUTE=Explore"
close $identity
if {[llength [get_runs $synth_name -quiet]]} { delete_runs [get_runs $synth_name] }
if {[llength [get_runs $impl_name -quiet]]} { delete_runs [get_runs $impl_name] }
create_run $synth_name -flow [get_property FLOW [get_runs synth_1]] \
  -strategy [get_property STRATEGY [get_runs synth_1]] -constrset constrs_1
clone_steps synth_1 $synth_name
create_run $impl_name -parent_run [get_runs $synth_name] \
  -flow [get_property FLOW [get_runs impl_1]] \
  -strategy [get_property STRATEGY [get_runs impl_1]] -constrset constrs_1
clone_steps impl_1 $impl_name
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED 0 [get_runs $impl_name]
set_property STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE Explore [get_runs $impl_name]
launch_runs $synth_name -jobs 2 -dir $build_dir
wait_on_run $synth_name
if {![string match "*Complete*" [get_property STATUS [get_runs $synth_name]]]} { error "synthesis failed" }
launch_runs $impl_name -to_step route_design -jobs 2 -dir $build_dir
wait_on_run $impl_name
puts "EXPLORE_STATUS=[get_property STATUS [get_runs $impl_name]]"
if {![string match "*Complete*" [get_property STATUS [get_runs $impl_name]]]} { error "implementation failed" }
open_run $impl_name
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
  -file [file join $evidence current_timing_summary_explore.rpt]
check_timing -verbose -file [file join $evidence current_check_timing_explore.rpt]
report_route_status -file [file join $evidence current_route_status_explore.rpt]
report_drc -file [file join $evidence current_drc_explore.rpt]
report_cdc -file [file join $evidence current_cdc_explore.rpt]
report_methodology -file [file join $evidence current_methodology_explore.rpt]
report_utilization -hierarchical -file [file join $evidence current_utilization_explore.rpt]
write_checkpoint -force [file join $evidence current_routed_explore.dcp]
close_project
exit
