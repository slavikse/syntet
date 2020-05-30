<template>
  <div class="App">
    <div class="routers">
      <div class="title">
        ПРОЕКТЫ
      </div>

      <div class="buttons">
        <router-link
          :to="{ name: 'TicTacToe' }"
          class="route"
        >
          Крестики нолики <span>(В разработке)</span>
        </router-link>

        <router-link
          :to="{ name: 'Square' }"
          class="route"
        >
          Квадрат в лабиринте <span>(Завершён)</span>
        </router-link>

        <router-link
          :to="{ name: 'Bird' }"
          class="route"
        >
          Плоская птица <span>(Приостановлен)</span>
        </router-link>
      </div>
    </div>

    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',

  data() {
    return {
      prevRouteName: localStorage.getItem('prevRouteName'),
    };
  },

  watch: {
    $route(to) {
      if (to.meta.isReload && to.name !== this.prevRouteName) {
        localStorage.setItem('prevRouteName', to.name);
        window.location.reload();
      }
    },
  },
};
</script>

<style scoped>
.App {
}

.title {
  margin-bottom: 10px;
  font-weight: bold;
  font-size: 20px;
}

.routers {
  position: absolute;
  top: 0;
  z-index: 1;
  padding: 20px;
  color: gray;
}

.buttons {
  display: flex;
  flex-direction: column;
}

.routers .route {
  margin-top: 5px;
  color: gray;
  cursor: pointer;
  text-decoration: none;
}

.routers .route.router-link-exact-active {
  font-weight: bold;
}

.routers .route:visited {
  color: gray;
}

.routers .route span {
  font-size: 13px;
  color: dimgray;
}
</style>
