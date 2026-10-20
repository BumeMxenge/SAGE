// A burst of confetti when the account is created, as the prototype's: discs and ribbons in the course
// colours that fall once from just above the page, drifting, turning and fading. It is decoration only,
// and isn't drawn at all under reduced motion.
import styles from './Confetti.module.css'

// Each piece's place across the page, drift, turn, start, length of fall and size, from fixed sums
// rather than chance, so every visit, and every screenshot, gets the same burst. They follow the
// prototype's ranges: 46 pieces from 2 to 98% across, drifting up to about 140 px and turning up to 540
// degrees, setting off within about a second, some falling further, and so faster, than others. Every
// fourth piece is a disc of 6 to 9 px; the rest are ribbons of 5 to 8 by 10 to 16 px.
const pieces = Array.from({ length: 46 }, (_, index) => ({
  across: 2 + ((index * 37) % 97),
  drift: ((index * 53) % 23) - 11,
  turn: ((index * 71) % 1081) - 540,
  delay: ((index * 29) % 11) / 33,
  distance: 0.8 + ((index * 41) % 13) / 25,
  size: (index % 4 === 0 ? 0.75 : 0.625) + ((index * 17) % 7) / 16,
}))

export function Confetti() {
  return (
    <div aria-hidden="true" className={styles.confetti}>
      {pieces.map(({ across, drift, turn, delay, distance, size }) => (
        <span
          key={across}
          className={styles.piece}
          style={{
            '--across': `${across}%`,
            '--drift': `${drift}vw`,
            '--turn': `${turn}deg`,
            '--delay': delay,
            '--distance': distance,
            '--size': size,
          }}
        />
      ))}
    </div>
  )
}
