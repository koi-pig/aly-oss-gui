PROJECT_URL = "https://github.com/koi-pig/aly-oss-gui"

HELP_HTML = """
<h2>使用方法</h2>
<p><b>项目地址：</b><a href="https://github.com/koi-pig/aly-oss-gui">https://github.com/koi-pig/aly-oss-gui</a></p>
<ol>
<li><b>OSS 配置</b><br>
第一次启动如果没有 config.local.json，会自动弹出“OSS 配置”窗口。<br>
AccessKey ID、AccessKey Secret、Bucket 都要填你自己的。</li>
<li><b>Bucket</b><br>
Bucket 要改成自己阿里云 OSS 里的 Bucket 名称，不要用别人的示例值。</li>
<li><b>Endpoint</b><br>
Endpoint 要和 Bucket 所在地域一致，例如 http://oss-cn-hangzhou.aliyuncs.com。</li>
<li><b>大文件上传</b><br>
软件会自动使用 OSS 分片并发上传。默认：分片阈值 10MB，每片 8MB，线程数 16。</li>
<li><b>上传结果</b><br>
上传完成后会自动复制链接，并在“最后上传链接”中显示。</li>
</ol>
<p>作者 QQ 2557745606<br>by koi-pig</p>
"""
