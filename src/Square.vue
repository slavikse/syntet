<template>
  <div>
    <div class="stat time">
      {{ time }} / Прошло секунд: {{ startTime }}.
    </div>

    <div class="stat epoch">
      Эпоха: {{ epoch }}
    </div>

    <div
      ref="Square"
      class="Square"
      tabindex="0"
      @keyup.up="jumpTop"
      @keyup.right="jumpRight"
      @keyup.down="jumpBottom"
      @keyup.left="jumpLeft"
    >
      <div class="cells field">
        <div
          v-for="(cell, index) in field"
          :key="index"
          :class="['cell', {
            'available': cell === 1,
            'starting-checkpoint': cell === 8,
            'finishing-checkpoint': cell === 9,
          }]"
        >
          <div
            v-if="cell === 8"
            class="starting-checkpoint"
          >
            СТАРТ
          </div>

          <div
            v-if="cell === 9"
            class="finishing-checkpoint"
          >
            ФИНИШ
          </div>
        </div>
      </div>

      <div class="players field">
        <div class="player">
          🐥
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';

export default {
  name: 'Square',

  data() {
    return {
      time: Date(),
      startTime: 0,
      style: undefined,

      // Игровая область обязательно квадратной формы.
      // 0 - Запретная территория.
      // 1 - Проходная территория.
      // 8 - Начальная точка.
      // 9 - Финишная точка.
      field: [
        8, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 1, 9,
      ],
      size: -1,
      quantityColumns: -1,
      quantityRows: -1,

      actor: {
        x: 1,
        y: 1,
        delay: 100,
      },

      model: tf.sequential(),
      // Порог прохождения (вероятность) для принятия решения.
      threshold: 0.4,
      epoch: 0,
      training: {
        // [x, y] - Нормализованные координаты актёра.
        inputs: [],
        // [1, 0, 0, 0] - Пойти на север (north).
        // [0, 1, 0, 0] - Пойти на восток (east).
        // [0, 0, 1, 0] - Пойти на юг (south).
        // [0, 0, 0, 1] - Пойти на запад (west).
        labels: [],
      },
      modelPredictId: undefined,
    };
  },

  watch: {
    'actor.x': 'setPlayerStyleProperties',
    'actor.y': 'setPlayerStyleProperties',
  },

  mounted() {
    this.setupModel();

    // Timer.
    setInterval(() => {
      this.time = Date();
      this.startTime += 1;
    }, 1000);

    this.style = this.$refs.Square.style;

    this.settingPlayingField();
    this.setPlayerStyleProperties();
  },

  destroyed() {
    clearTimeout(this.modelPredictId);
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        // [x, y] - Нормализованные координаты актёра.
        inputShape: [2],
        activation: 'sigmoid', // todo relu ???
        units: 10,
      }));

      this.model.add(tf.layers.dense({
        inputShape: [10],
        activation: 'sigmoid',
        // [north, east, south, west] - Прогноз стороны для передвижения.
        units: 4,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.1),
        loss: 'meanSquaredError',
      });
    },

    settingPlayingField() {
      this.size = Math.sqrt(this.field.length);
      this.quantityColumns = this.size;
      this.quantityRows = this.size;

      this.style.setProperty('--quantity-columns', this.quantityColumns);
      this.style.setProperty('--quantity-rows', this.quantityRows);
    },

    setPlayerStyleProperties() {
      const { x, y } = this.actor;

      this.style.setProperty('--player-column', x);
      this.style.setProperty('--player-row', y);

      this.checkExit();
    },

    async checkExit() {
      clearTimeout(this.modelPredictId);

      const { x, y } = this.actor;
      let label = [];

      switch (true) {
        // north
        case y < 1:
          label = [-1, 1, 1, 1];
          break;

        // east
        case x > this.size:
          label = [1, -1, 1, 1];
          break;

        // south
        case y > this.size:
          label = [1, 1, -1, 1];
          break;

        // west
        case x < 1:
          label = [1, 1, 1, -1];
          break;

        default:
          label = [];
      }

      // console.log('label', [...label]);
      // console.log('actor', { ...this.actor });

      const cell = this.field[(x - 1) + (y - 1) * this.size];

      if (cell === 0) {
        label = [-0.5, -0.5, -0.5, -0.5];
      }

      if (label.length > 0) {
        await this.modelFit({ label });
        this.resetGame();
      }

      this.modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
    },

    async modelFit({ label }) {
      let isRunInputs = true;
      let { x, y } = this.actor;
      // console.log('fit x, y', x, y);

      // todo на следующей ячейке производится оценка.
      // if (x === 1 && y === this.size + 1) {
      //   isRunInputs = false;
      //   console.log('ПОЧТИ!', x, y);
      //   label = [0.5, 0.5, 0.5, 0.5];
      //
      //   // TODO !!!
      //   this.training.inputs.push([
      //     x / this.size,
      //     (y - 1) / this.size,
      //   ]);
      // }

      // todo на следующей ячейке производится оценка.
      if (x === this.size + 1 && y === this.size + 1) {
        isRunInputs = false;
        console.log('ФИНИШ!');
        label = [10, 10, 10, 10];

        // TODO !!!
        this.training.inputs.push([
          (x - 1) / this.size,
          (y - 1) / this.size,
        ]);
      }

      if (isRunInputs) {
        // todo до выяснения
        if (x > 1) {
          x -= 1;
        }

        if (y > 1) {
          y -= 1;
        }

        this.training.inputs.push([
          x / this.size,
          y / this.size,
        ]);
      }

      this.training.labels.push(label);

      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );
    },

    resetGame() {
      console.log('RESET GAME');

      this.actor = {
        ...this.actor,
        x: 1,
        y: 1,
      };
    },

    async modelPredict() {
      const { x, y } = this.actor;

      const prediction = this.model.predict(tf.tensor2d([
        [
          x / this.size,
          y / this.size,
        ],
      ]));

      const [jumpTop, jumpRight, jumpBottom, jumpLeft] = await prediction.data();
      console.log('T, R, B, L', jumpTop, jumpRight, jumpBottom, jumpLeft);

      let maximum = jumpTop;
      let action = 'jumpTop';

      if (jumpRight > maximum) {
        maximum = jumpRight;
        action = 'jumpRight';
      }

      if (jumpBottom > maximum) {
        maximum = jumpBottom;
        action = 'jumpBottom';
      }

      if (jumpLeft > maximum) {
        maximum = jumpLeft;
        action = 'jumpLeft';
      }

      // console.log('maximum /', maximum, action);

      if (maximum > this.threshold) {
        this[action]();
      }

      this.modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
    },

    jumpTop() {
      this.actor.y -= 1;
    },

    jumpRight() {
      this.actor.x += 1;
    },

    jumpBottom() {
      this.actor.y += 1;
    },

    jumpLeft() {
      this.actor.x -= 1;
    },
  },
};
</script>

<style
  lang='scss'
  scoped
>
.Square {
  --quantity-rows: -1;
  --quantity-columns: -1;
  --column-width: 5rem;

  --player-row: -1;
  --player-column: -1;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;
  user-select: none;
}

.stat {
  position: absolute;
  z-index: 1;
  font-size: 1.2rem;
  color: white;
}

.time {
  left: 0.5rem;
}

.epoch {
  right: 0.5rem;
  font-size: 1.4rem;
}

.cells {
  .cell {
    display: flex;
    background-color: #222;
  }

  .available {
    background-color: darkcyan;
  }

  .starting-checkpoint,
  .finishing-checkpoint {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    line-height: 0.9;
    font-weight: bold;
  }

  .starting-checkpoint {
    background-color: yellowgreen;
    outline: 0.5rem dashed yellowgreen;
  }

  .finishing-checkpoint {
    background-color: seagreen;
    outline: 0.5rem dashed seagreen;
  }
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--column-width));
  grid-template-columns: repeat(var(--quantity-columns), var(--column-width));
  grid-gap: 1rem;
}

.players {
  position: absolute;

  .player {
    grid-row: var(--player-row);
    grid-column: var(--player-column);
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 2.4rem;
    background-color: yellow;
    outline: 0.5rem dashed yellow;
  }
}
</style>
