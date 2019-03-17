<template>
  <div
    class="Car"
    tabindex="0"
  >
    <div class="epoch">
      Эпоха: {{ epoch }}
    </div>

    <div class="time">
      {{ time }}
    </div>

    <div class="lanes">
      <div
        v-for="lane in quantityLanes"
        :key="lane"
        :data-index="lane - 1"
        class="lane"
      >
      </div>

      <div
        :style="{ transform: `translate(${enemyLane * laneSize}rem, ${enemyTop}rem)` }"
        class="enemy"
      />

      <div
        v-for="(lane, index) in quantityLanes - 1"
        :key="lane + 100"
        :style="getRoadMarkingStyle(index)"
        class="road-marking"
      >
      </div>
    </div>

    <div class="player" />
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import cloneDeep from 'clone-deep';

const collisionHeight = 60;
const maxCollisionHeight = 60;

function getRandom(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}

export default {
  name: 'Car',

  data() {
    return {
      // При больших значениях из за округлений вычислений начинают смещаться полосы.
      quantityLanes: 4,
      laneSize: 4,
      roadMarkingSize: 0.1,
      currentLane: 0,
      turnTime: 200,
      enemyAnimTime: 300,

      model: undefined,
      training: undefined,
      epoch: 0,
      time: Date(),

      enemyTop: 0,
      enemyLane: 0,
    };
  },

  mounted() {
    this.setStyleProperties();
    this.handleReset();

    setInterval(() => {
      this.time = Date();
    }, 1000);

    // Проверка средой на столкновения.
    setInterval(() => {
      this.enemyTop += 10;

      if (this.currentLane === this.enemyLane && this.enemyTop === collisionHeight) {
        console.log(`BOOM L${this.currentLane} | timestamp:${Date.now()}`);

        const label = new Array(this.quantityLanes).fill(1);
        label[this.currentLane] = 0;

        this.handleCrash({ label: cloneDeep(label) });
      }

      if (this.enemyTop >= maxCollisionHeight) {
        this.enemyTop = 0;
        // this.enemyLane = (this.enemyLane + 1) % this.quantityLanes;
        this.enemyLane = getRandom(0, this.quantityLanes);
      }
    }, this.enemyAnimTime);

    // Оценщик.
    setInterval(this.handleRunning, 500);
  },

  methods: {
    handleReset() {
      this.model = tf.sequential();

      this.model.add(tf.layers.dense({
        inputShape: [2],
        activation: 'sigmoid',
        units: 10,
      }));

      this.model.add(tf.layers.dense({
        inputShape: [10],
        activation: 'sigmoid',
        units: 4,
      }));

      this.model.compile({ loss: 'meanSquaredError', optimizer: tf.train.adam(0.1) });

      this.training = {
        // [Расстояние до врага, Текущая линия врага (выбирается случайно)]
        inputs: [],
        // Рассчитывается в зависимости от количества дорожек: this.quantityLanes.
        // К примеру сторон = 4:
        // [0, 1, 1, 1] - перейти с дорожки 0.
        // [1, 0, 1, 1] - перейти с дорожки 1.
        // [1, 1, 0, 1] - перейти с дорожки 2.
        // [1, 1, 1, 0] - перейти с дорожки 3.
        labels: [],
      };
    },

    handleRunning() {
      return new Promise(() => {
        const prediction = this.model.predict(tf.tensor2d([
          cloneDeep([
            this.enemyTop / maxCollisionHeight,
            this.enemyLane / (this.quantityLanes - 1),
          ]),
        ]));

        prediction.data().then(([l0, l1, l2, l3]) => {
          console.log(l0, l1, l2, l3);

          let threshold = 0.5;

          let maximum = l0;
          let lane = 0;
          let title = 'L0';

          if (l1 > maximum) {
            maximum = l1;
            lane = 1;
            title = 'L1';
          }

          if (l2 > maximum) {
            maximum = l2;
            lane = 2;
            title = 'L2';
          }

          if (l3 > maximum) {
            maximum = l3;
            lane = 3;
            title = 'L3';
          }

          if (maximum > threshold) {
            console.log(`${title} prediction: ${maximum}`);
            this.currentLane = lane;
            this.setCurrentLane();
          }
        });
      });
    },

    handleCrash({ label }) {
      this.training.inputs.push(
        cloneDeep([
          this.enemyTop / maxCollisionHeight,
          this.enemyLane / (this.quantityLanes - 1),
        ]),
      );
      // console.log(cloneDeep([
      //   this.enemyTop / maxCollisionHeight,
      //   this.enemyLane / (this.quantityLanes - 1),
      // ]));

      console.log('label', cloneDeep(label));
      this.training.labels.push(cloneDeep(label));

      this.handleTrain();
    },

    handleTrain() {
      // console.log(this.training.inputs);
      // console.log(this.training.labels);

      this.model.fit(
        tf.tensor2d(cloneDeep(this.training.inputs)),
        tf.tensor2d(cloneDeep(this.training.labels)),
      );

      this.epoch += 1;
    },

    setStyleProperties() {
      const { style } = document.documentElement;

      style.setProperty('--quantity-lanes', this.quantityLanes);
      style.setProperty('--lane-size', `${this.laneSize}rem`);
      style.setProperty('--road-marking-size', `${this.roadMarkingSize}rem`);
      style.setProperty('--turn-time', `${this.turnTime}ms`);
      style.setProperty('--enemy-anim-time', `${this.enemyAnimTime}ms`);

      this.setCurrentLane();
    },

    setCurrentLane() {
      const { style } = document.documentElement;
      style.setProperty('--current-lane', this.currentLane);
    },

    getRoadMarkingStyle(index) {
      const bias = this.laneSize - this.roadMarkingSize;
      return { left: `${(index + 1) * bias}rem` };
    },
  },
};
</script>

<style>
:root {
  /* Вводимые переменные из JS. Объявление для корректной подсветки IDE. */
  --quantity-lanes: -1;
  --lane-size: -1rem;
  --road-marking-size: -1rem;
  --current-lane: -1;
  --turn-time: -1ms;
  --enemy-anim-time: -1ms;

  --field-size: calc(var(--lane-size) * var(--quantity-lanes));
  --main-indent: calc(50% - var(--field-size) / 2);

  --player-size: 3rem;
  --player-current-lane: calc(var(--lane-size) * var(--current-lane));

  --bg-color: #284242;
  --lane-color: darkslategray;
  --border-lane-color: #607d8b;
  --player-color: aliceblue;

  --enemy-color: greenyellow;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}
</style>

<style scoped>
.Car {
  background-color: var(--bg-color);
  outline: none;
}

.epoch {
  position: absolute;
  z-index: 1;
  top: 3rem;
  right: 1rem;
  font-size: 1.5rem;
  color: white;
}

.time {
  position: absolute;
  z-index: 1;
  left: 0.5rem;
  font-size: 1.1rem;
  color: white;
}

.lanes {
  position: relative;
  margin-left: var(--main-indent);
  display: flex;
  width: var(--field-size);
  border: var(--road-marking-size) solid var(--border-lane-color);
  border-top: none;
  border-bottom: none;
  overflow: hidden;
}

.lane {
  position: relative;
  width: var(--lane-size);
  height: 100vh;
  background-color: var(--lane-color);
}

.lane::before {
  position: absolute;
  bottom: 0;
  width: 100%;
  text-align: center;
  font-size: 2rem;
  color: white;
  content: "L" attr(data-index);
}

.road-marking {
  --bias: 1.9rem;
  position: absolute;
  top: calc(var(--bias) * -1);
  height: calc(var(--bias) + 100vh);
  border-right: var(--road-marking-size) dashed var(--border-lane-color);
  animation: road-marking 0.3s infinite linear;
  will-change: transform;
}

@keyframes road-marking {
  to {
    transform: translateY(var(--bias));
  }
}

.enemy {
  position: absolute;
  top: 0;
  margin: 0 0.5rem;
  height: 0.6rem;
  width: 3rem;
  border-radius: 0.5rem;
  background-color: var(--enemy-color);
  transition: transform var(--enemy-anim-time) linear;
  will-change: transform;
}

.player {
  position: absolute;
  bottom: 4rem;
  /* Просто +0.5rem... */
  left: calc(var(--main-indent) + 0.5rem);
  width: var(--player-size);
  height: 7rem;
  background: url('./assets/car.png') no-repeat 100% / cover;
  transform: translateX(var(--player-current-lane));
  transition: var(--turn-time) transform ease-in-out;
  will-change: transform;
}
</style>
