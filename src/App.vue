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
          Крестики нолики <span>(Завершён)</span>

          <a
            href="https://habr.com/ru/post/505574"
            target="_blank"
            class="link"
            @click.stop
          >
            _Статья__
          </a>
        </router-link>

        <router-link
          :to="{ name: 'Square' }"
          class="route"
        >
          Квадрат в лабиринте <span>(Завершён)</span>

          <a
            href="https://habr.com/ru/post/452612"
            target="_blank"
            class="link"
            @click.stop
          >
            _Статья__
          </a>
        </router-link>

        <router-link
          :to="{ name: 'Snake' }"
          class="route"
        >
          Змейка <span>(В разработке)</span>
        </router-link>

        <router-link
          :to="{ name: 'Bird' }"
          class="route"
        >
          Птица <span>(Приостановлен)</span>
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

<style
  lang="scss"
  scoped
>
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
  padding: 10px;
  color: gray;

  .route {
    margin-top: 5px;
    color: gray;
    text-decoration: none;

    &:visited {
      color: gray;
    }

    &.router-link-exact-active {
      font-weight: bold;
    }

    .link {
      color: white;

      &:visited {
        color: white;
      }
    }
  }

  .route span {
    font-size: 13px;
    color: dimgray;
  }
}

.buttons {
  display: flex;
  flex-direction: column;
}
</style>
