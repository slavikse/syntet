import Vue from 'vue';
import VueRouter from 'vue-router';

import App from '@/App.vue';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    name: 'App',
    meta: { isReload: false },
    component: App,
    redirect: { name: 'TicTacToe' },
  },
  {
    path: '/TicTacToe',
    name: 'TicTacToe',
    meta: { isReload: true },
    component: () => import('@/TicTacToe.vue'),
  },
  {
    path: '/Square',
    name: 'Square',
    meta: { isReload: true },
    component: () => import('@/Square.vue'),
  },
  {
    path: '/Bird',
    name: 'Bird',
    meta: { isReload: true },
    component: () => import('@/Bird.vue'),
  },
];

const router = new VueRouter({
  mode: 'history',
  routes,
});

export default router;
