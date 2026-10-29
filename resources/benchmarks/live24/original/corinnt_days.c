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