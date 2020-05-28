import Vue from 'vue';

import App from '@/App.vue';
import router from './router';

Vue.config.productionTip = false;
Vue.config.silent = process.env.NODE_ENV === 'production';

new Vue({
  name: 'App',
  router,
  render: (h) => h(App),
}).$mount('#app');
