import Vue from 'vue';
import VueRouter from 'vue-router';

import App from '@/App.vue';
import TicTacToe from '@/TicTacToe.vue';
import Square from '@/Square.vue';

import Snake from '@/Snake.vue';
// import Puppet from '@/Puppet.vue';
// import Cart from '@/Cart.vue';
// import Bird from '@/Bird.vue';

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
    path: '/Snake',
    name: 'Snake',
    meta: { isReload: true },
    component: Snake,
  },
  // {
  //   path: '/Puppet',
  //   name: 'Puppet',
  //   meta: { isReload: true },
  //   component: Puppet,
  // },
  // {
  //   path: '/Cart',
  //   name: 'Cart',
  //   meta: { isReload: true },
  //   component: Cart,
  // },
  // {
  //   path: '/Bird',
  //   name: 'Bird',
  //   meta: { isReload: true },
  //   component: Bird,
  // },
];

export default new VueRouter({ routes });
