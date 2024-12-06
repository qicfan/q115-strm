<script setup lang="ts">
import MarkdownIt from 'markdown-it'
const md = new MarkdownIt()
const content = `
### 一、介绍
本服务支持将115网盘的内容通过目录树方式生成本地STRM文件，如果有元服务需求也可以用复制或者软链方式同步到本地（元数据不支持webdav）

相对于终端脚本，docker版本新增特性如下：
- 支持添加多个同步目录
- 每个同步目录单独设置类型(local, alist)
- 每个同步目录可以登录不同的115账号（每个115账号要是不同的挂载根目录）
- 同步目录支持定时同步或者监控变更（只支持CD2，可能遗漏，具体取决于CD2或者115）
`
const result = md.render(content)
</script>
<template>
  <div class="greetings" v-html="result"></div>
</template>

<style scoped></style>
