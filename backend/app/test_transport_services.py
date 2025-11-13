from services.road_services.AnalyzeOnRoadForMultiProcessing import AnalyzeOnRoadForMultiprocessing
from multiprocessing import freeze_support


if __name__ == '__main__':
    freeze_support()
    analyzer = AnalyzeOnRoadForMultiprocessing(
        show_log= True,
        show= True, 
        is_join_processes= True
    )
    analyzer.run_multiprocessing()
    