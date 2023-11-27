\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \relative c'{\numericTimeSignature c g' c, e g e g2 e4 g c,2 g' e e4 c g' c, e2 c4 e g c, e g c,1 \bar "|."}

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
