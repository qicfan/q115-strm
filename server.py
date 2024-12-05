
# libs - 监控的媒体库
#   path - 115相对路径
#   name - 自定义名称
#   watch - 是否监控文件变更自动触发同步: 1-开启，2-关闭
#   status - 状态：1-正常，2-同步中，3-未完成（每次请求时会检查，如果同步中但是PID不存在则会改为3）
#   pid - 处于同步中时的进程ID，可以根据PID强行停止
#   created_at - 添加时间
#   last_sync_at - 最后一次同步时间
#   last_sync_result - 最后一次同步结果