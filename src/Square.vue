<template>
  <div>
    <div class="stat time">
      Прошло секунд: {{ startTime }}
    </div>

    <div class="stat epoch">
      Шаг: {{ actor.step }} | Эпоха: {{ epoch }} | Побед: {{ win }}
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
            'starting-checkpoint': cell === 7,
            'middle-checkpoint': cell === 8,
            'finishing-checkpoint': cell === 9,
          }]"
        >
          <div
            v-if="cell === 7"
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

function getRandomArbitrary(min, max) {
  return Math.random() * (max - min) + min;
}

let maxActorStep = -1;

// todo вместо 8 - точки подкрепления - на каждом следующем шаге,
//   давать чуть больше подкрепления, чем на предыдущем,
//   что будет поддталкивать пройти дальше.

// todo помечать пройденные ячейки, как заблокированные и возвращать при сброче обратно.

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
        0, 0, 0, 0, 0, 0, 0,
        0, 7, 0, 0, 0, 0, 0,
        0, 1, 0, 0, 0, 0, 0,
        0, 1, 0, 0, 0, 0, 0,
        0, 1, 0, 0, 0, 0, 0,
        0, 8, 1, 1, 1, 9, 0,
        0, 0, 0, 0, 0, 0, 0,
      ],
      size: -1,
      quantityColumns: -1,
      quantityRows: -1,

      actor: {
        x: 2,
        y: 2,
        step: 0,
        delay: 20,
      },

      model: tf.sequential(),
      epoch: 0,
      win: 0,
      training: {
        // [x, y, step] - Нормализованные координаты актёра.
        // step - количество шагов, сделанных со стартовой позиции.
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

  async mounted() {
    maxActorStep = this.field.length;

    this.setupModel();

    // Timer.
    setInterval(() => {
      this.time = Date();
      this.startTime += 1;
    }, 1000);

    this.style = this.$refs.Square.style;

    this.settingPlayingField();
    await this.setPlayerStyleProperties();
    this.checkExit();
  },

  destroyed() {
    clearTimeout(this.modelPredictId);
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        // [x, y, step] - Нормализованные координаты актёра.
        // step - количество шагов, сделанных со стартовой позиции.
        inputShape: [3],
        activation: 'sigmoid',
        units: 10,
      }));

      // this.model.add(tf.layers.dense({
      //   inputShape: [10],
      //   activation: 'sigmoid',
      //   units: 10,
      // }));

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

    async setPlayerStyleProperties() {
      const { x, y } = this.actor;

      this.style.setProperty('--player-column', x);
      this.style.setProperty('--player-row', y);

      // TODO
      if (this.actor.step >= maxActorStep) {
        clearTimeout(this.modelPredictId);
        await this.modelFit();
        this.modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
      }
    },

    async checkExit() {
      const { x, y, step } = this.actor;
      const cell = this.field[(x - 1) + (y - 1) * this.size];

      let label = [0, 0, 0, 0];
      // Тренировать на накопленных training.inputs при выходе за границы.
      let isModelFit = false;

      if (cell === 0) {
        label = [
          getRandomArbitrary(-0.5, 0.2),
          getRandomArbitrary(-0.5, 0.2),
          getRandomArbitrary(-0.5, 0.2),
          getRandomArbitrary(-0.5, 0.2),
        ];

        isModelFit = true;
      }

      if (cell === 1) {
        label = [
          getRandomArbitrary(0.5, 0.8),
          getRandomArbitrary(0.5, 0.8),
          getRandomArbitrary(0.5, 0.8),
          getRandomArbitrary(0.5, 0.8),
        ];
      }

      if (cell === 7) {
        label = [
          getRandomArbitrary(0.1, 0.3),
          getRandomArbitrary(0.1, 0.3),
          getRandomArbitrary(0.1, 0.3),
          getRandomArbitrary(0.1, 0.3),
        ];
      }

      if (cell === 8) {
        label = [
          getRandomArbitrary(1, 1.4),
          getRandomArbitrary(1, 1.4),
          getRandomArbitrary(1, 1.4),
          getRandomArbitrary(1, 1.4),
        ];
      }

      if (cell === 9) {
        console.log('ФИНИШ!', x, y);

        label = [
          getRandomArbitrary(1.5, 2),
          getRandomArbitrary(1.5, 2),
          getRandomArbitrary(1.5, 2),
          getRandomArbitrary(1.5, 2),
        ];

        this.win += 1;
        isModelFit = true;
      }

      // console.log('cell', cell, 'label', label);

      this.training.inputs.push([
        (x - 1) / this.size,
        (y - 1) / this.size,
        step / maxActorStep,
      ]);

      this.training.labels.push(label);

      if (isModelFit) {
        await this.modelFit();
      }

      this.modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
    },

    async modelFit() {
      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );

      await this.resetGame();
    },

    async resetGame() {
      this.epoch += 1;

      this.actor = {
        ...this.actor,
        x: 2,
        y: 2,
        step: 0,
      };

      await this.setPlayerStyleProperties();
    },

    async modelPredict() {
      const { x, y, step } = this.actor;

      const prediction = this.model.predict(tf.tensor2d([
        [
          x / this.size,
          y / this.size,
          step / maxActorStep,
        ],
      ]));

      const [jumpTop, jumpRight, jumpBottom, jumpLeft] = await prediction.data();

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

      this[action]();
      this.actor.step += 1;

      await this.setPlayerStyleProperties();
      this.checkExit();
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
  .middle-checkpoint,
  .finishing-checkpoint {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    line-height: 0.9;
    font-weight: bold;
    background-color: seagreen;
    outline: 0.5rem dashed seagreen;
  }

  .middle-checkpoint {
    background-color: greenyellow;
    outline: 0.5rem dashed greenyellow;
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
