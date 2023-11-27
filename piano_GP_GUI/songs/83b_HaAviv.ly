\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key g \major \relative c'{\time 3/4 s2 d4 | g g g | a d, d | a' a a | b g d' | d b8 d b d | c4 a c | c a8 c a c | b2 d4 | g8 fis e d c b | d4 c a | d,8 e fis g a fis | g2 \bar "|."}

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
