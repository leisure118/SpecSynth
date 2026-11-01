/*@
  requires 1 <= month <= 12;
  assigns \nothing;
  ensures month == 1 ==> \result == 31;
  ensures month == 2 ==> \result == 28;
  ensures month == 3 ==> \result == 31;
  ensures month == 4 ==> \result == 30;
  ensures month == 5 ==> \result == 31;
  ensures month == 6 ==> \result == 30;
  ensures month == 7 ==> \result == 31;
  ensures month == 8 ==> \result == 31;
  ensures month == 9 ==> \result == 30;
  ensures month == 10 ==> \result == 31;
  ensures month == 11 ==> \result == 30;
  ensures month == 12 ==> \result == 31;
*/
int day_of(int month){
    int days[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 } ;
    return days[month-1] ;
}
int main(){
    int days2 = day_of(2);
    //@ assert days2 == 28;
    int days7 = day_of(7);
    //@ assert days7 == 31;
}
