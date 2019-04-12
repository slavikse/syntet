<template>
  <div
    ref="root"
    class="Bird"
    tabindex="0"
    @keydown.up="agentUp"
  >
    <div class="field">
      <div
        v-for="agent in agents"
        :key="agent.id"
        :style="{ transform: `translate(${agent.x}rem, ${-agent.y}rem)` }"
        :class="['agent', { intersected: agent.isIntersected }]"
      />

      <div
        v-for="wall in walls"
        :key="wall.id"
        :style="{ transform: `translate(${wall.x}rem, ${-wall.y}rem)` }"
        class="wall"
      />
    </div>
  </div>
</template>

<!-- todo добавить функционал: для того, чтобы начать - нажми -->
<!-- todo адаптивность под размеры экрана. -->
<!-- todo гибкость переменных. константы. initialValue и тд. -->
<script>
import TWEEN from '@tweenjs/tween.js';

let rafId;

const agentState = {
  heightUp: { y: 14 },
  heightDown: { y: 0 },
  flightTime: 400,
  tween: { stop() {} },
};

const wallMovementTime = 5000;

export default {
  name: 'Bird',

  data() {
    return {
      agents: [
        {
          id: `agents_${1}`,
          x: 1,
          y: 0,
          width: 5,
          height: 5,
          isIntersected: false,
        },
      ],
      walls: [
        {
          id: `walls_${1}`,
          x: 20,
          y: 4,
          width: 2,
          height: 4,
          from: {
            x: 20,
          },
          to: {
            x: -2,
          },
        },
        {
          id: `walls_${2}`,
          x: 22,
          y: 8,
          width: 2,
          height: 4,
          from: {
            x: 20,
          },
          to: {
            x: -2,
          },
        },
      ],
    };
  },

  mounted() {
    rafId = requestAnimationFrame(this.gameLoop);

    this.agentSetting();
    this.wallsMovement();
  },

  destroyed() {
    cancelAnimationFrame(rafId);
  },

  methods: {
    gameLoop(time) {
      rafId = requestAnimationFrame(this.gameLoop);
      TWEEN.update(time);
    },

    // todo
    agentSetting() {
      const [agent] = this.agents;
      const [wall] = this.walls;

      this.$refs.root.style.setProperty('--agent-width', `${agent.width}rem`);
      this.$refs.root.style.setProperty('--agent-height', `${agent.height}rem`);

      this.$refs.root.style.setProperty('--wall-width', `${wall.width}rem`);
      this.$refs.root.style.setProperty('--wall-height', `${wall.height}rem`);
    },

    agentUp() {
      agentState.tween.stop();

      // todo
      const [agent] = this.agents;

      agentState.tween = new TWEEN.Tween(agent)
        .to(agentState.heightUp, agentState.flightTime)
        .easing(TWEEN.Easing.Quadratic.Out)
        .onComplete(this.agentDown)
        .start();
    },

    agentDown() {
      // todo
      const [agent] = this.agents;

      agentState.tween = new TWEEN.Tween(agent)
        .to(agentState.heightDown, agentState.flightTime)
        .easing(TWEEN.Easing.Quadratic.In)
        .onComplete(this.agentFell)
        .start();
    },

    agentFell() {
      console.log('agentFell');
    },

    // todo
    wallsMovement() {
      const [wall] = this.walls;

      new TWEEN.Tween(wall)
        .to(wall.to, wallMovementTime)
        .onUpdate(this.hasIntersect)
        .onComplete(this.wallsMovementEnd)
        .start();
    },

    // todo
    hasIntersect() {
      const [agent] = this.agents;
      const [wall] = this.walls;

      if (
        // Правая граница агента.
        (agent.x + agent.width) > wall.x
        // Верхняя граница агента.
        && (agent.y + agent.height) > wall.y
        // Нижняя граница агента.
        && agent.y < (wall.y + wall.height)
      ) {
        // todo являетя окончаем игры агента.
        agent.isIntersected = true;

        // todo del
        setTimeout(() => {
          agent.isIntersected = false;
        }, 1000);
      }
    },

    // todo
    wallsMovementEnd() {
      this.walls[0].x = this.walls[0].from.x;

      this.wallsMovement();
    },
  },
};
</script>

<style scoped>
.Bird {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;

  --agent-width: -1rem;
  --agent-height: -1rem;

  --wall-width: -1rem;
  --wall-height: -1rem;
}

.field {
  position: relative;
  width: 20rem;
  height: 20rem;
  background-color: #222;
  overflow: hidden;
}

/* todo ширина высота из js */
.agent {
  position: absolute;
  bottom: 0;
  width: var(--agent-width);
  height: var(--agent-height);
  background-color: forestgreen;
  will-change: transform;
}

.agent.intersected {
  background-color: yellowgreen;
}

.wall {
  position: absolute;
  bottom: 0;
  width: var(--wall-width);
  height: var(--wall-height);
  background-color: brown;
  will-change: transform;
}
</style>
