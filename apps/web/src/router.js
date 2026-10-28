import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.js'
import LauncherView from './views/LauncherView.js'
import RunView from './views/RunView.js'
import ResultView from './views/ResultView.js'
import SpectoolView from './views/SpectoolView.js'
import X509FunctionView from './views/X509FunctionView.js'

import ProjectsView from './views/ProjectsView.js'
import WorkspaceView from './views/WorkspaceView.js'

const routes = [
  { path: '/projects', component: ProjectsView },
  { path: '/projects/:id', component: WorkspaceView },
  { path: '/', component: HomeView },
  { path: '/upload', component: LauncherView },
  { path: '/spectool', component: SpectoolView },
  { path: '/run/:id', component: RunView },
  { path: '/result/:id', component: ResultView },
  { path: '/x509-function/:name', component: X509FunctionView },
]

export default createRouter({ history: createWebHashHistory(), routes })
