<template>
  <div class="App">
    <div class="O r1-c1" />
    <div class="O r1-c2" />
    <div class="O r1-c3" />

    <div class="O r2-c1" />
    <div class="X r2-c2" />
    <div class="O r2-c3" />

    <div class="O r3-c1" />
    <div class="X r3-c2" />
    <div class="O r3-c3" />

    <div class="O r4-c1" />
    <div class="O r4-c2" />
    <div class="O r4-c3" />

    <div class="actor" />
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';

let model;
let training;

// todo отрицательное подкрепление при неудачном выборе хода.
// todo положительное подкрепление только по прохождению лабиринта.

export default {
  name: 'App',

  mounted() {
    this.reset();
  },

  methods: {
    reset() {
      model = tf.sequential();
      // [1, 0, 0, 0] - вверх.
      // [0, 1, 0, 0] - вправо.
      // [0, 0, 1, 0] - вниз.
      // [0, 0, 0, 1] - влево.
      model.add(tf.layers.dense({ inputShape: [4], activation: 'sigmoid', units: 10 }));
      model.add(tf.layers.dense({ inputShape: [10], activation: 'sigmoid', units: 10 }));
      model.add(tf.layers.dense({ inputShape: [10], activation: 'sigmoid', units: 4 }));
      model.compile({ loss: 'meanSquaredError', optimizer: tf.train.adam(0.1) });

      training = {
        // Значения на входе.
        inputs: [],
        // Интерпретация значений входа.
        labels: [],
      };

      setInterval(() => {
        this.predict();
      }, 1000);
    },

    predict() {
      return new Promise(() => {
        // todo алгоритм должен предлагать варианты
        // todo среда должна поощрять актёра за предпринятые действия.
        const prediction = model.predict(tf.tensor2d([[0, 1, 0, 0]]));

        prediction.data().then(([top, right, bottom, left]) => {
          console.log('predict', top, right, bottom, left);

          // if (top > 0.5) {
          //   // todo принимать решение о поощрении и наказании нужно только по завершению игры.
          //   // todo сейчас игра состоит из 1 шага.
          //   const { style } = document.documentElement;
          //   style.setProperty('--row', 2);
          //
          //   this.train({ input: [top, bottom], label: [1, 0] });
          // } else {
          //   this.train({ input: [top, bottom], label: [0, 1] });
          // }
        });
      });
    },

    train({ input, label }) {
      training.inputs.push(input);
      training.labels.push(label);
    },

    fit() {
      console.log('fit', training);
      model.fit(tf.tensor2d(training.inputs), tf.tensor2d(training.labels));
    },
  },
};
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  height: 100vh;
  background-color: #333;
}

:root {
  --row: 3;
  --col: 2;
}
</style>

<style
  lang="scss"
  scoped
>
.App {
  padding: 10rem 5rem 0 0;
  display: grid;
  justify-content: end;
  grid-template-rows: repeat(4, 6rem);
  grid-template-columns: repeat(3, 6rem);
  grid-gap: 0.5rem;
}

.actor {
  margin: auto;
  grid-row: var(--row);
  grid-column: var(--col);
  width: 40%;
  height: 40%;
  border-radius: 50%;
  background-color: dodgerblue;
}

.X,
.O {
  &::after {
    display: block;
    padding-left: 0.5rem;
    color: white;
    font-size: 1.2rem;
  }
}

.X {
  grid-area: X;
  background-color: darkgreen;
}

.O {
  grid-area: O;
  background-color: brown;
}

.r1-c1 {
  grid-row: 1;
  grid-column: 1;

  &::after {
    content: "r1-c1";
  }
}

.r1-c2 {
  grid-row: 1;
  grid-column: 2;

  &::after {
    content: "r1-c2";
  }
}

.r1-c3 {
  grid-row: 1;
  grid-column: 3;

  &::after {
    content: "r1-c3";
  }
}

.r2-c1 {
  grid-row: 2;
  grid-column: 1;

  &::after {
    content: "r2-c1";
  }
}

.r2-c2 {
  grid-row: 2;
  grid-column: 2;

  &::after {
    content: "r2-c2";
  }
}

.r2-c3 {
  grid-row: 2;
  grid-column: 3;

  &::after {
    content: "r2-c3";
  }
}

.r3-c1 {
  grid-row: 3;
  grid-column: 1;

  &::after {
    content: "r3-c1";
  }
}

.r3-c2 {
  grid-row: 3;
  grid-column: 2;

  &::after {
    content: "r3-c2";
  }
}

.r3-c3 {
  grid-row: 3;
  grid-column: 3;

  &::after {
    content: "r3-c3";
  }
}

.r4-c1 {
  grid-row: 4;
  grid-column: 1;

  &::after {
    content: "r4-c1";
  }
}

.r4-c2 {
  grid-row: 4;
  grid-column: 2;

  &::after {
    content: "r4-c2";
  }
}

.r4-c3 {
  grid-row: 4;
  grid-column: 3;

  &::after {
    content: "r4-c3";
  }
}
</style>
