<template>
  <div
    class="App"
    tabindex="0"
    @keydown="laneChangeDebounced"
  >
    <div class="lanes">
      <div
        v-for="lane in quantityLanes"
        :key="lane"
        class="lane"
      >
        <div class="enemy" />
      </div>

      <div
        v-for="(lane, index) in quantityLanes - 1"
        :key="lane + 100"
        :style="getRoadMarkingStyle(index)"
        class="road-marking"
      >
      </div>
    </div>

    <div class="player player-turns" />
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import debounce from 'lodash.debounce';

const leftKeyCode = 37;
const rightKeyCode = 39;

export default {
  name: 'App',

  data() {
    return {
      // При больших значениях из за округлений вычислений начинают смещаться полосы.
      quantityLanes: 2,
      laneSize: 4,
      roadMarkingSize: 0.1,
      currentLane: 0,
      turnTime: 200,
      laneChangeDebounced: debounce(this.laneChange, this.turnTime),

      model: undefined,
      training: undefined,
      currentTime: 0,
      maximumTime: 3,
      // todo признак, что сторона была изменена. каждые 5 секунд сбрасывается.
      isTriggered: false,
    };
  },

  mounted() {
    this.setStyleProperties();
    this.handleReset();

    setInterval(() => {
      this.currentTime += 1;
      this.handleRunning();
    }, 1000);

    setInterval(() => {
      if (!this.isTriggered) {
        this.handleCrash(0, this.maximumTime);
      }

      this.isTriggered = false;
      this.currentTime = 0;
      this.handleTrain();
    }, this.maximumTime * 1000);

    // Подталкивающий метод. Случайная смена стороны.
    setInterval(() => {
      if (this.currentLane === 0) {
        this.currentLane = 1;
      } else {
        this.currentLane = 0;
      }

      this.setCurrentLane();

      this.isTriggered = true;
      const time = JSON.parse(JSON.stringify(this.currentTime));
      this.handleCrash(1, time);
      console.log('ШАЛОСТЬ УДАЛАСЬ');
    }, (this.maximumTime + 2) * 1000);
  },

  methods: {
    handleReset() {
      this.model = tf.sequential();
      this.model.add(tf.layers.dense({ inputShape: [1], activation: 'sigmoid', units: 6 }));
      this.model.add(tf.layers.dense({ inputShape: [6], activation: 'sigmoid', units: 1 }));
      this.model.compile({ loss: 'meanSquaredError', optimizer: tf.train.adam(0.1) });

      this.training = {
        // Входное время.
        inputs: [],
        // Действие: 0 - ничего, 1 - сменить сторону.
        labels: [],
      };
    },

    handleRunning() {
      const time = JSON.parse(JSON.stringify(this.currentTime));

      return new Promise(() => {
        const prediction = this.model.predict(tf.tensor2d([[time / this.maximumTime]]));

        prediction.data().then(([pred]) => {
          if (pred > 0.5) {
            if (this.currentLane === 0) {
              this.currentLane = 1;
            } else {
              this.currentLane = 0;
            }

            this.setCurrentLane();

            this.isTriggered = true;
            this.handleCrash(1, time);
            console.log('yes', pred);
          } else {
            console.log('no', pred);
          }
        });
      });
    },

    handleCrash(train, time) {
      const trainS = JSON.parse(JSON.stringify(train));
      const timeS = JSON.parse(JSON.stringify(time));

      this.training.inputs.push([timeS / this.maximumTime]);
      this.training.labels.push([trainS]);
    },

    handleTrain() {
      // console.log('Training', this.training.inputs);
      // console.log(this.training.labels);
      this.model.fit(tf.tensor2d(this.training.inputs), tf.tensor2d(this.training.labels));
    },

    setStyleProperties() {
      const { style } = document.documentElement;

      style.setProperty('--quantity-lanes', this.quantityLanes);
      style.setProperty('--lane-size', `${this.laneSize}rem`);
      style.setProperty('--road-marking-size', `${this.roadMarkingSize}rem`);
      style.setProperty('--turn-time', `${this.turnTime}ms`);

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

    laneChange({ keyCode }) {
      switch (keyCode) {
        case leftKeyCode:
          this.laneLeft();
          break;

        case rightKeyCode:
          this.laneRight();
          break;

        default:
      }

      this.setCurrentLane();
    },

    laneLeft() {
      if (this.currentLane > 0) {
        this.currentLane -= 1;
      }
    },

    laneRight() {
      if (this.currentLane < this.quantityLanes - 1) {
        this.currentLane += 1;
      }
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
.App {
  background-color: var(--bg-color);
  outline: none;
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
  width: var(--lane-size);
  height: 100vh;
  background-color: var(--lane-color);
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

/* todo передвижение */
.enemy {
  margin: 0 0.5rem;
  height: 0.6rem;
  border-radius: 0.5rem;
  background-color: var(--enemy-color);
  transform: translateY(1rem);
  transition: transform 0.1s;
  will-change: transform;
}

/* todo при смене дорожки, поворот машинки */
/* todo проезжаемые объекты по краям дороги */
.player {
  position: absolute;
  bottom: 4rem;
  /* Просто +0.5rem... */
  left: calc(var(--main-indent) + 0.5rem);
  width: var(--player-size);
  height: 7rem;
  background: url('./assets/car.png') no-repeat 100% / cover;
  transform: translateX(var(--player-current-lane));
  /*transition: var(--turn-time) transform ease-in-out;*/
  will-change: transform;
}

.player-turns {
  /*--angleRotation: 4deg;*/
  /*transform: rotate(10deg);*/
  /*transform-origin: bottom;*/
  /*animation: player-turns 1s alternate infinite ease-in-out;*/
}

/* todo разобраться как */
@keyframes player-turns {
  from {
    transform: translateX(var(--player-current-lane)) rotate(var(--angleRotation));
  }

  to {
    /* todo */
    transform: translateX(var(--player-current-lane)) rotate(calc(var(--angleRotation) * -1));
  }
}
</style>
