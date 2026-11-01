import { defineComponent, computed } from 'vue'
import { useRoute } from 'vue-router'
export default defineComponent({
  setup() { const route = useRoute(); return { workspace: computed(() => route.path.startsWith('/projects/') || route.path.startsWith('/benchmarks/') || route.path === '/spectool'), home: computed(() => route.path === '/'), projectsPage: computed(() => route.path === '/projects') } },
  template: `<div class="app-layout" :class="{'vf-workspace-layout':workspace,'vf-projects-layout':projectsPage}">
    <a class="skip-link" href="#main-content" @click.prevent="$refs.mainContent.focus()">跳到主要内容</a>
    <header v-if="!workspace" class="app-header" :class="{'vf-home-header':home}"><div class="header-inner">
      <router-link to="/" class="logo" aria-label="玄鉴首页"><span class="xuanjian-brand"><img class="xuanjian-symbol" src="/brand/favicon.svg" alt=""><span class="xuanjian-name">玄鉴<span class="xuanjian-sub">AI 赋能的可信软件智能验证</span></span></span></router-link>
      <nav class="header-nav" aria-label="主导航"><router-link to="/projects" class="nav-link" active-class="active">项目</router-link><router-link to="/spectool" class="nav-link" active-class="active">工具箱</router-link><span class="vf-local">本地工作区</span></nav>
    </div></header>
    <main ref="mainContent" id="main-content" class="app-main" tabindex="-1"><router-view /></main>
    <footer v-if="!workspace" class="app-footer"><span>© {{new Date().getFullYear()}} 玄鉴 · ACSL Agent</span><span>ACSL · Frama-C · 形式化验证</span></footer>
  </div>`
})
