\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key f \major \relative c'{\numericTimeSignature f4 f g8 f4. | f4 f g8 f4. | f4 f g8 f e f | g2 c,2 | bes'8 g g g g g g4 | a8 f f f f f f4 | c4 bes' a8 a g g | c1 | d8 g, g g g g g4 | a8 f f f f f f4 | c4 bes' a8 a g g | f1 \bar "|."} 

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
