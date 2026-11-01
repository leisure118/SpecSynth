/*@
  requires 1 <= m <= 12;
  assigns \nothing;
  ensures m == 1 ==> \result == 31;
  ensures m == 2 ==> \result == 28;
  ensures m == 3 ==> \result == 31;
  ensures m == 4 ==> \result == 30;
  ensures m == 5 ==> \result == 31;
  ensures m == 6 ==> \result == 30;
  ensures m == 7 ==> \result == 31;
  ensures m == 8 ==> \result == 31;
  ensures m == 9 ==> \result == 30;
  ensures m == 10 ==> \result == 31;
  ensures m == 11 ==> \result == 30;
  ensures m == 12 ==> \result == 31;
*/
int day_of(int m){
    int days[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
    return days[m-1];
}
int main(){
    int m2 = day_of(2);
    //@ assert m2 == 28;
    int m1 = day_of(1);
    //@ assert m1 == 31;
    int m4 = day_of(4);
    //@ assert m4 == 30;
    return 0;
}
