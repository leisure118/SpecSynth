import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.js'
import RunView from './views/RunView.js'
import ResultView from './views/ResultView.js'
import SpectoolView from './views/SpectoolView.js'
import X509FunctionView from './views/X509FunctionView.js'

import ProjectsView from './views/ProjectsView.js'
import WorkspaceView from './views/WorkspaceView.js'
import SkillsView from './views/SkillsView.js'
import DatasetView from './views/DatasetView.js'

import BenchmarkView from './views/BenchmarkView.js'

const routes = [
  { path: '/benchmarks/:id', component: BenchmarkView },
  { path: '/skills', component: SkillsView },
  { path: '/datasets/nl2vbench', component: DatasetView },
  { path: '/projects', component: ProjectsView },
  { path: '/projects/:id', component: WorkspaceView },
  { path: '/', component: HomeView },
  { path: '/upload', redirect: to => ({path:'/projects',query:{...to.query,...(!to.query.demo?{new:'1'}:{})},hash:to.hash}) },
  { path: '/spectool', component: SpectoolView },
  { path: '/run/:id', component: RunView },
  { path: '/result/:id', component: ResultView },
  { path: '/x509-function/:name', component: X509FunctionView },
]

export default createRouter({ history: createWebHashHistory(), routes })
