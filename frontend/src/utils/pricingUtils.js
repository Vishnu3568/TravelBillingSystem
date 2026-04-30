/**
 * Transport Billing Calculation Engine
 * 
 * Business Rules:
 * 1. Base Package (Local): 8 Hours / 80 KM -> ₹2800
 * 2. Extra KM: (Total KM - 80) * ₹16 (If Total KM <= 200)
 * 3. Extra Hours: (Total Hours - 8) * ₹130
 * 4. Long Trip (Total KM > 200):
 *    - SEDAN: ₹14/km
 *    - CRYSTA: ₹18/km
 */

export const calculateCharges = (totalKm, totalHours, vehicleType) => {
  const km = parseFloat(totalKm) || 0;
  const hours = parseFloat(totalHours) || 0;
  const vType = (vehicleType || "SEDAN").toUpperCase();

  let charges = [];
  let pricingType = "BASE";

  if (km > 200) {
    pricingType = "PER_KM";
    const rate = vType === "CRYSTA" ? 18 : 14;
    const amount = km * rate;
    
    charges.push({
      name: "Distance Charge",
      calc: `${km}x${rate}`,
      amount: amount,
      isSystem: true
    });
  } else {
    pricingType = "BASE";
    
    // 1. Base Amount
    charges.push({
      name: "Base Amount",
      calc: "8/80",
      amount: 2800,
      isSystem: true
    });

    // 2. Extra KM
    if (km > 80) {
      const extraKm = km - 80;
      const amount = extraKm * 16;
      charges.push({
        name: "Extra KM",
        calc: `${extraKm}x16`,
        amount: amount,
        isSystem: true
      });
    }

    // 3. Extra Hours
    if (hours > 8) {
      const extraHours = hours - 8;
      const amount = extraHours * 130;
      charges.push({
        name: "Extra Hours",
        calc: `${extraHours}x130`,
        amount: amount,
        isSystem: true
      });
    }
  }

  const totalAmount = charges.reduce((sum, c) => sum + c.amount, 0);

  return {
    pricingType,
    charges,
    totalAmount
  };
};
