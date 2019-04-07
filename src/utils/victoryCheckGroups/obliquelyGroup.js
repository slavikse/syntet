import verticalGroup from './verticalGroup';

// Выигрышные наборы для третьей группы:
//  1.  2.
// X** **X
// *X* *X*
// **X X**

// Проверка 1 и 2 наборов.
export default function obliquelyGroup({ cells, sign }) {
  return verticalGroup({ cells, sign, start: 0, step: 3 })
    || verticalGroup({ cells, sign, start: 2, step: 1 });
}
