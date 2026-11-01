int grade;
/*@
  assigns grade;
  ensures (1 <= mark && mark <= 100) ==> \result == 1;
  ensures (101 <= mark && mark <= 200) ==> \result == 2;
  ensures (201 <= mark && mark <= 300) ==> \result == 3;
  ensures (301 <= mark && mark <= 400) ==> \result == 4;
  ensures (mark < 1 || mark > 400) ==> \result == 0;
*/
int calculateGrade(int mark) {
    if (mark >= 1 && mark <= 100) {
        grade = 1;
        return grade;
    } else if (mark >= 101 && mark <= 200) {
        grade = 2;
        return grade;
    } else if (mark >= 201 && mark <= 300) {
        grade = 3;
        return grade;
    } else if (mark >= 301 && mark <= 400) {
        grade = 4;
        return grade;
    }
    return 0;
}
