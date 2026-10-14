import { Icon } from '@/components/Icon/Icon.tsx'
import { iconNames } from '@/components/Icon/icons.ts'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function IconsSection() {
  return (
    <Section
      title="Icons"
      intro="Every icon the screens use, from Material Symbols Rounded. An icon takes only its name, and filled where a filled version exists. The name is what you pass to Icon."
    >
      <div className={styles.iconGrid}>
        {iconNames.map((name) => (
          <div key={name} className={styles.iconCell}>
            {name === 'favorite' ? <Icon name="favorite" /> : <Icon name={name} />}
            <span>{name}</span>
          </div>
        ))}
        <div className={styles.iconCell}>
          <Icon name="favorite" filled />
          <span>favorite, filled</span>
        </div>
      </div>
    </Section>
  )
}
