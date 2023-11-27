\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key f \major \relative c'{\numericTimeSignature s2. c4 a'2 f4 f g2 c,4 c f e f a g2. a4 bes bes a bes c2 a4 f a a g a bes2 g4 d' c2 a4 c bes2 g4 d' c a bes g f2. \bar "|."}

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
