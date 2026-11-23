无  
智能体     

现在不做任何接口的封装，两个智能体之间以裸数据接口的方式传递数据  
运维智能体对下一个智能体暴露的方法：（假设instance名为ops）  
ops.start()     (执行初始化流程)  
ops.close()     (关闭)  
目前公开方法里不对event做任何处理  
对下一个智能体暴露的变量:  
ops.topology_manager.topology       (全网拓扑)  
ops.topology_manager.cluster_graph      (簇图)  
ops.link_budget_analyzer.services        (所有业务、包含背景和测试业务、下一智能体只需读取测试业务)  
ops.link_budget_analyzer.residual_bw       (所有链路的剩余带宽)  