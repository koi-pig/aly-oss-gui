# 阿里云 OSS 文件管理工具

项目地址：https://github.com/koi-pig/aly-oss-gui

这是一个 PySide6 桌面工具，支持选择 Bucket、上传文件、显示上传进度、按原 OSS 链接覆盖文件、查看文件列表、复制链接和删除文件。

## 打包 exe

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File ./build_exe.ps1
```

每次打包会删除 `dist` 目录里的旧 exe，只保留最终版 `dist/AlyOssTool.exe`。

## 生成配置文件

第一次启动时，如果软件同目录没有 `config.local.json`，程序会自动弹出“OSS 配置”窗口。填写后点击保存，会自动生成配置文件。

## 配置字段

```json
{
  "access_key_id": "你的 AccessKey ID",
  "access_key_secret": "你的 AccessKey Secret",
  "bucket": "你自己的 Bucket 名称",
  "endpoint": "http://oss-cn-<region>.aliyuncs.com",
  "upload_endpoint": "",
  "view_endpoint": "https://%s.oss-cn-<region>.aliyuncs.com/%s",
  "signed_url_expire_seconds": 315360000,
  "page_size": 10,
  "multipart_threshold_mb": 10,
  "multipart_part_size_mb": 16,
  "multipart_threads": 32
}
```

`bucket` 必须改成你自己的 OSS Bucket 名称。

`endpoint` 要写 Bucket 对应的阿里云 OSS 地域地址。示例：

```text
杭州: http://oss-cn-hangzhou.aliyuncs.com
上海: http://oss-cn-shanghai.aliyuncs.com
北京: http://oss-cn-beijing.aliyuncs.com
```

大文件上传会自动启用分片并发上传：

- `multipart_threshold_mb`：文件大于等于多少 MB 启用分片上传，默认 10。
- `multipart_part_size_mb`：每个分片大小，默认 16。大文件可试 16 或 32。
- `multipart_threads`：并发上传线程数，默认 32。网络不稳定时改回 16 或 8。

- `upload_endpoint`：上传专用 Endpoint，可填 OSS 传输加速地址，例如 `https://oss-accelerate.aliyuncs.com`。留空时使用 `endpoint`。

## 批量上传

点击“选择文件”时可以多选文件。多选后点击“上传”，软件会按当前 OSS 路径的目录前缀并发上传多个文件，进度按所有文件总大小统计。
## 列表排序

默认“快速分页”直接使用 OSS 分页，刷新最快。切换为“最新优先”时，软件会扫描当前前缀下的对象，再按 OSS 更新时间倒序分页显示，最新修改、最接近当前时间的文件排在最前面。
## 列表速度说明

为了保证刷新速度，文件列表不逐条读取对象元数据。创建时间按 OSS 更新时间显示，到期时间默认显示永不过期。