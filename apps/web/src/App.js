import { defineComponent, computed } from 'vue'
import { useRoute } from 'vue-router'
import LanguageSwitcher from './components/LanguageSwitcher.js'
import {elementLocale} from './i18n.js'
export default defineComponent({
  components:{LanguageSwitcher},
  setup() { const route = useRoute(); return { elementLocale, workspace: computed(() => route.path.startsWith('/projects/') || route.path.startsWith('/benchmarks/') || route.path === '/spectool'), home: computed(() => route.path === '/'), projectsPage: computed(() => route.path === '/projects') } },
  template: `<el-config-provider :locale="elementLocale"><LanguageSwitcher/><div class="app-layout" :class="{'vf-workspace-layout':workspace,'vf-projects-layout':projectsPage,'cover-layout':true,'cover-home-layout':home}">
    <a class="skip-link" href="#main-content" @click.prevent="$refs.mainContent.focus()">{{ $t("跳到主要内容") }}</a>
    <header v-if="!workspace && !home" class="app-header" :class="{'vf-home-header':home}"><div class="header-inner">
      <router-link to="/" class="logo"><span class="xuanjian-brand"><img class="xuanjian-symbol" src="/brand/favicon.svg" alt=""><span class="xuanjian-name">{{ $t("玄鉴") }}</span></span></router-link>
      <nav class="header-nav" :aria-label="$t(&quot;主导航&quot;)"><router-link to="/projects" class="nav-link" active-class="active">{{ $t("项目") }}</router-link><router-link to="/spectool" class="nav-link" active-class="active">{{ $t("工具箱") }}</router-link><span class="vf-local">{{ $t("本地工作区") }}</span></nav>
    </div></header>
    <main ref="mainContent" id="main-content" class="app-main" tabindex="-1"><router-view /></main>
    <footer v-if="!workspace && !home" class="app-footer"><span>{{ $t("© ") }}{{ $t(new Date().getFullYear()) }}{{ $t(" 玄鉴 · ACSL Agent") }}</span><span>{{ $t("C / ACSL · Rust / Verus · 形式化验证") }}</span></footer>
  </div></el-config-provider>`
})
