<template>
  <div
    ref="snake"
    tabindex="-1"
    class="Snake"
    @keyup.up="step('stepTop')"
    @keyup.right="step('stepRight')"
    @keyup.down="step('stepBottom')"
    @keyup.left="step('stepLeft')"
  >
    <div class="field">
      <div
        v-for="(barrier, index) in field"
        :key="index"
        :style="{ backgroundColor: barrier }"
        class="cell"
      >
        {{ rewards[index] }}
      </div>
    </div>

    <div class="actor">
      <div class="field">
        <div
          v-for="({ position }, index) in actor.cells"
          :key="index"
          :style="{
            gridColumn: position.x,
            gridRow: position.y,
          }"
          class="cell"
        />
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import cloneDeep from 'clone-deep';

const fieldSize = 10;
const cellEmpty = '';
const barrierSign = '#111';
const appleSign = 'brown';

const basicReward = 0.1;
const barrierReward = -1;
const appleReward = 1;

export default {
  name: 'Snake',

  data() {
    return {
      model: tf.sequential(),
      training: { inputs: [], labels: [] },
      rewards: Array(fieldSize ** 2).fill(basicReward),

      field: Array(fieldSize ** 2).fill(cellEmpty),
      fieldSize,

      actor: {
        cells: [
          { position: { x: 3, y: 6 } },
          { position: { x: 3, y: 7 } },
          { position: { x: 3, y: 8 } },
        ],
        step: 1,
      },
      actorDefault: undefined,
    };
  },

  mounted() {
    this.actorDefault = cloneDeep(this.actor);

    this.setupModel();

    this.setStyle();
    this.resetCells();
    this.markCells();

    // todo добавление яблока
    this.field[45] = appleSign;
    this.rewards[45] = appleReward;

    // todo test
    this.$forceUpdate();
  },

  methods: {
    // todo
    setupModel() {
      this.model.add(tf.layers.dense({
        inputShape: [this.fieldSize],
        activation: 'sigmoid',
        units: 64,
      }));

      // model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 24,
      // }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: 4,
      }));

      this.model.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });
    },

    setStyle() {
      this.$refs.snake.style.setProperty('--rows', String(fieldSize));
      this.$refs.snake.style.setProperty('--columns', String(fieldSize));
    },

    resetCells() {
      for (let x = 0; x < fieldSize; x += 1) {
        for (let y = 0; y < fieldSize; y += 1) {
          const cellIndex = y * fieldSize + x;

          // Границы поля.
          if (x === 0 || x === fieldSize - 1 || y === 0 || y === fieldSize - 1) {
            this.field[cellIndex] = barrierSign;
            this.rewards[cellIndex] = barrierReward;
          } else {
            this.field[cellIndex] = cellEmpty;
            this.rewards[cellIndex] = basicReward;
          }
        }
      }
    },

    markCells() {
      this.actor.cells.forEach(({ position: { x, y } }) => {
        const cellIndex = (y - 1) * fieldSize + (x - 1);

        this.field[cellIndex] = barrierSign;
        this.rewards[cellIndex] = barrierReward;
      });
    },

    step(side) {
      const { position: { x, y } } = this.actor.cells[this.actor.cells.length - 1];

      this.stepTails();
      this.resetTail({ x, y });
      this.stepHead(side);

      this.hasAvailability();
    },

    stepTails() {
      for (let i = this.actor.cells.length - 1; i > 0; i -= 1) {
        const cell = this.actor.cells[i];
        cell.position = this.actor.cells[i - 1].position;

        const { position: { x, y } } = cell;
        const cellIndex = (y - 1) * fieldSize + (x - 1);

        this.field[cellIndex] = barrierSign;
        this.rewards[cellIndex] = barrierReward;
      }
    },

    resetTail({ x, y }) {
      const cellIndex = (y - 1) * fieldSize + (x - 1);

      this.field[cellIndex] = cellEmpty;
      this.rewards[cellIndex] = basicReward;
    },

    // todo помечать голову как занятую ячейку
    stepHead(side) {
      const [cell] = this.actor.cells;
      this[side]({ cell, ...cell.position });
    },

    stepTop({ cell, x, y }) {
      cell.position = { x, y: y - 1 };
    },

    stepRight({ cell, x, y }) {
      cell.position = { x: x + 1, y };
    },

    stepBottom({ cell, x, y }) {
      cell.position = { x, y: y + 1 };
    },

    stepLeft({ cell, x, y }) {
      cell.position = { x: x - 1, y };
    },

    // todo после обновления в stepHead, может не правильно срабатывать?
    hasAvailability() {
      const [{ position: { x, y } }] = this.actor.cells;
      const cellIndex = (y - 1) * fieldSize + (x - 1);

      if (this.field[cellIndex] === barrierSign) {
        this.resetGame();
      }
    },

    resetGame() {
      this.actor = cloneDeep(this.actorDefault);
      this.resetCells();
    },
  },
};
</script>

<style
  lang="scss"
  scoped
>
.Snake {
  --rows: -1;
  --columns: -1;
  --size: 25px;

  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  user-select: none;
  outline: none;
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--rows), var(--size));
  grid-template-columns: repeat(var(--columns), var(--size));
  grid-gap: 1px;

  .cell {
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 10px;
    color: #9acd32;
    background-color: #444;
  }
}

.actor {
  position: absolute;

  .cell {
    /* todo */
    /*background-color: #9acd32;*/
    background-color: rgba(#9acd32, 0.4);
  }
}
</style>
