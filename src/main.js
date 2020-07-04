import Vue from 'vue';
import VueRouter from 'vue-router';

import App from '@/App.vue';
import TicTacToe from '@/TicTacToe/TicTacToe.vue';
import Square from '@/Square.vue';
import Snake from '@/Snake.vue';

// import Symbols from '@/Symbols.vue';
// import Puppet from '@/Puppet.vue';
// import Cart from '@/Cart.vue';
// import Bird from '@/Bird.vue';

Vue.use(VueRouter);

Vue.config.productionTip = false;
Vue.config.silent = process.env.NODE_ENV === 'production';

new Vue({
  name: 'App',
  render: (h) => h(App),
  router: new VueRouter({
    routes: [
      {
        path: '/',
        name: 'App',
        component: App,
        redirect: { name: 'TicTacToe' },
        meta: { isReload: false },
      },
      {
        path: '/TicTacToe',
        name: 'TicTacToe',
        component: TicTacToe,
        meta: { isReload: true },
      },
      {
        path: '/Square',
        name: 'Square',
        component: Square,
        meta: { isReload: true },
      },
      {
        path: '/Snake',
        name: 'Snake',
        component: Snake,
        meta: { isReload: true },
      },
      // {
      //   path: '/Symbols',
      //   name: 'Symbols',
      //   component: Symbols,
      //   meta: { isReload: true },
      // },
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
      // }, }),
    ],
  }),
}).$mount('#app');
