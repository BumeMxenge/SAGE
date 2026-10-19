// A burst of confetti when the account is created: small pieces in the course colours that fall,
// drift, turn and fade, once. It is decoration only, and isn't drawn at all under reduced motion.
import styles from './Confetti.module.css'

// Where each piece starts across the page, how far it drifts and turns, and how late it sets off, as a
// share of one fall. Fixed numbers, so every visit, and every screenshot, gets the same burst.
const pieces = Array.from({ length: 36 }, (_, index) => ({
  across: (index * 37) % 100,
  drift: ((index * 53) % 21) - 10,
  turn: (index * 71) % 360,
  delay: ((index * 29) % 10) / 40,
}))

export function Confetti() {
  return (
    <div aria-hidden="true" className={styles.confetti}>
      {pieces.map(({ across, drift, turn, delay }) => (
        <span
          key={across}
          className={styles.piece}
          style={{ '--across': `${across}%`, '--drift': `${drift}vw`, '--turn': `${turn}deg`, '--delay': delay }}
        />
      ))}
    </div>
  )
}
