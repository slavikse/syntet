import Vue from 'vue';
import VueRouter from 'vue-router';

import App from '@/App.vue';
import TicTacToe from '@/TicTacToe.vue';
import Square from '@/Square.vue';
import Bird from '@/Bird.vue';

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
    component: TicTacToe,
  },
  {
    path: '/Square',
    name: 'Square',
    meta: { isReload: true },
    component: Square,
  },
  {
    path: '/Bird',
    name: 'Bird',
    meta: { isReload: true },
    component: Bird,
  },
];

const router = new VueRouter({
  // mode: 'history',
  routes,
});

export default router;
