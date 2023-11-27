\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \relative c'{\numericTimeSignature c g'2 e4 g c, e2 g4 c, e c g' e2 g4 e c g' e c g' e2 c4 g'2 e4 c1 \bar "|."}

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
