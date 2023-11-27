\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key g \major \relative c'{\numericTimeSignature s2. d8 g b4 b8 a g4 a8 g e8 g4.~ g4 d8 g8 b4 g8 b d4 c8 b8 a2. d8 c b4 b8 a g4 a8 b d c4.~ c4 e,8 e d4 fis8 g a4 b8 a g2. \bar "|."}

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
