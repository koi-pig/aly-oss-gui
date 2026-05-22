HELP_TEXT = """使用方法

1. OSS 配置
   第一次启动如果没有 config.local.json，会自动弹出“OSS 配置”窗口。
   也可以在主界面点击“OSS 配置”修改并生成配置文件。
   保存后会写入软件同目录的 config.local.json。

2. 大文件上传速度
   软件会自动使用 OSS 分片并发上传。
   分片阈值 MB：文件大于等于该值时启用分片上传，默认 10。
   每片大小 MB：每个上传分片大小，默认 8。
   上传线程数：分片并发线程数，默认 16。
   网络好可以保持 16；如果失败或变慢，调回 8。

3. 配置字段
   AccessKey ID / AccessKey Secret：阿里云 OSS 的访问密钥。
   默认 Bucket：启动后默认使用的 Bucket，例如 rrbstorage。
   Endpoint：Bucket 所在地域地址，例如 http://oss-cn-hangzhou.aliyuncs.com。
   链接模板：一般保持 https://%s.oss-cn-hangzhou.aliyuncs.com/%s。
   签名默认秒数：复制签名链接时的默认过期秒数。
   默认每页数量：文件列表默认每页显示数量，例如 10 或 20。

4. 上传文件
   选择本地文件，填写 OSS 路径，例如 apps/test.apk，然后点击“上传”。
   大文件中断后，再次上传同一个本地文件到同一个 OSS 路径，会继续补传。

5. 链接过期设置
   选择“永不过期公开链接”会返回公开访问链接。
   选择“签名链接”会按“过期天数”生成带签名的临时链接。

6. 查看/修改/删除
   先选择 Bucket，再填写前缀，例如 apps/，点击“刷新列表”。
   选中文件后，可以下载打开、覆盖上传、复制链接或删除。

作者 QQ 2557745606
by koi-pig
"""
