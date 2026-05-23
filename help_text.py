PROJECT_URL = "https://github.com/koi-pig/aly-oss-gui"

HELP_HTML = """
<style>
body { font-family: "Microsoft YaHei", Arial, sans-serif; font-size: 14px; line-height: 1.65; }
h2 { margin: 0 0 12px 0; font-size: 22px; }
h3 { margin: 18px 0 8px 0; font-size: 16px; }
p { margin: 6px 0; }
ol { margin: 8px 0 0 24px; padding: 0; }
li { margin: 8px 0; }
.meta { margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #dddddd; }
.muted { color: #555555; }
</style>
<h2>使用帮助 / 作者</h2>
<div class="meta">
<p><b>作者：</b>koi-pig</p>
<p><b>QQ：</b>2557745606</p>
<p><b>项目地址：</b><a href="https://github.com/koi-pig/aly-oss-gui">https://github.com/koi-pig/aly-oss-gui</a></p>
</div>
<h3>使用方法</h3>
<ol>
<li><b>OSS 配置：</b>第一次启动如果没有 config.local.json，会自动弹出“OSS 配置”窗口。AccessKey ID、AccessKey Secret、Bucket 都要填写你自己的。</li>
<li><b>Bucket：</b>Bucket 要改成自己阿里云 OSS 里的 Bucket 名称，不要使用别人的示例值。</li>
<li><b>Endpoint：</b>Endpoint 要和 Bucket 所在地域一致，例如 http://oss-cn-hangzhou.aliyuncs.com。</li>
<li><b>大文件上传：</b>软件会自动使用 OSS 分片并发上传。默认分片阈值 10MB，每片 16MB，线程数 32；网络不稳定可把线程数改小。</li>
<li><b>上传结果：</b>上传完成后会自动复制链接，并在“最后上传链接”中显示。</li>
<li><b>批量上传：</b>选择文件时可多选，软件会按当前 OSS 路径的目录前缀并发上传多个文件。</li>
<li><b>时间显示：</b>新上传文件会记录创建时间和到期时间。老文件没有记录时，创建时间按 OSS 更新时间显示，到期时间显示为永不过期。</li>
<li><b>列表排序：</b>默认快速分页，刷新很快；选择“最新优先”时会扫描当前前缀，把最新修改、最接近当前时间的文件排在前面。</li>
<li><b>上传加速：</b>配置里的上传 Endpoint 可填写 OSS 传输加速地址，例如 https://oss-accelerate.aliyuncs.com；留空则使用普通 Endpoint。</li>
</ol>
<p class="muted">配置文件保存在程序同目录的 config.local.json，打包 exe 后也放在 exe 同目录。</p>
"""
