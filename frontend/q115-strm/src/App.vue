<script setup lang="ts">
import type { AxiosStatic } from 'axios'
import { inject, ref } from 'vue'
import Home from './components/Home.vue'
import Settings from './components/Settings.vue'

const http: AxiosStatic | undefined = inject('$http')
http?.get('http://localhost:5000/settings').then((resp) => {
  console.log(resp.data)
})
console.log(http)
const currentMenu = ref('home')

function switchMenu(value: string) {
  console.log(value)
  currentMenu.value = value
}
</script>

<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <div>
          <div class="title">Q115-STRM</div>
          <div class="desc">通过115目录树快速生成STRM，集成登录、目录树功能</div>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <el-menu @select="switchMenu" :default-active="currentMenu">
            <el-menu-item index="home">
              <el-icon><HomeFilled /></el-icon> 使用说明
            </el-menu-item>
            <el-menu-item index="libs">
              <el-icon><Film /></el-icon> 同步目录
            </el-menu-item>
            <el-menu-item index="settings">
              <el-icon><Setting /></el-icon>设置
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <Home v-if="currentMenu == 'home'"></Home>
          <Settings v-if="currentMenu == 'settings'"></Settings>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped></style>
