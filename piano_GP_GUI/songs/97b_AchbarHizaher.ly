\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key f \major \relative c'{\time 4/4 f4 f8 g a4 a | g8 f g a f4 c | a' a8 bes c4 c | bes8 a bes c a2 | c4 c d2 | bes4 bes8 d8 c2 | a4 f bes g | c c f,2 \bar "|."} 

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
