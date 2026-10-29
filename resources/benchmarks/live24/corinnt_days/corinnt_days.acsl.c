/*@
  requires 1 <= month <= 12;
  ensures \result == ((month == 2) ? 28 : ((month == 4 || month == 6 || month == 9 || month == 11) ? 30 : 31));
  assigns \nothing;
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