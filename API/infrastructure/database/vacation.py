from datetime import datetime

from API.infrastructure.database.models import Base

import datetime
import typing
import uuid
from sqlalchemy import (BigInteger, Column, String, select, Date,
                        DateTime, func, Integer, ForeignKey, Boolean, update,
                        desc, not_, VARCHAR, Text, CHAR, JSON, DECIMAL, FLOAT)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship


class StaffVacation(Base):
    __tablename__ = "staff_vacation"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fullname = Column(String)
    iin = Column(String, unique=True)
    date_receipt: Column[datetime.datetime] = Column(DateTime)
    guid = Column(String, unique=True, nullable=True)
    is_fired = Column(Boolean, default=False)

    @classmethod
    async def get_by_iin(
            cls,
            iin: str,
            session: AsyncSession
    ) -> typing.Optional['StaffVacation']:
        stmt = select(StaffVacation).where(iin == StaffVacation.iin)

        return await session.scalar(stmt)

    @classmethod
    async def get_by_guid(
            cls,
            guid: str,
            session: AsyncSession
    ) -> typing.Optional['StaffVacation']:
        stmt = select(StaffVacation).where(guid == StaffVacation.guid)

        return await session.scalar(stmt)

    @classmethod
    async def get_all_user(
            cls,
            session: AsyncSession
    ) -> typing.Sequence['StaffVacation']:
        stmt = select(StaffVacation).where(StaffVacation.is_fired == False)
        response = await session.execute(stmt)
        return response.scalars().all()

    vacation = relationship(
        "VacationDays",
        lazy="selectin",
        #back_populates="staff"
        primaryjoin="StaffVacation.id == VacationDays.staff_vac_id",
        #uselist=True
    )


    @classmethod
    async def get_by_fuzzy_name(
            cls,
            name: str,
            session: AsyncSession
    ) -> typing.Optional['StaffVacation']:
        # Поиск без учета регистра (ILIKE)
        stmt = select(StaffVacation).where(StaffVacation.fullname.ilike(f"%{name}%"))
        # Вернем первого найденного
        return await session.scalar(stmt)


class VacationDays(Base):
    __tablename__ = "vacation_days"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    staff_vac_id = Column(
        BigInteger,
        ForeignKey("staff_vacation.id", onupdate='CASCADE', ondelete='CASCADE')
    )
    year = Column(Integer)
    days = Column(Integer)
    dbl_days = Column(DECIMAL(10, 4), nullable=False, default=0.0)
    vacation_start: Column[datetime.datetime] = Column(DateTime, default=None)
    vacation_end: Column[datetime.datetime] = Column(DateTime, default=None)
    vacation_code = Column(String, default=None)

    @classmethod
    async def get_staff_vac_days_by_year(
            cls,
            year: int,
            staff_id: int,
            session: AsyncSession
    ) -> typing.Optional['VacationDays']:
        stmt = select(VacationDays).where(
            (year == VacationDays.year) & (VacationDays.staff_vac_id == staff_id)
        )

        return await session.scalar(stmt)

    @classmethod
    async def get_vac_days_by_year(
            cls,
            year: int,
            session: AsyncSession
    ) -> typing.Sequence['VacationDays']:
        stmt = select(VacationDays).where(year == VacationDays.year)
        response = await session.execute(stmt)
        return response.scalars().all()

    @classmethod
    async def get_staff_vac_by_id(
            cls,
            staff_id,
            session: AsyncSession
    ) -> typing.Sequence['VacationDays']:
        stmt = select(VacationDays).where(VacationDays.staff_vac_id == staff_id).order_by(VacationDays.year)
        response = await session.execute(stmt)

        return response.scalars().all()


class VacationHistory(Base):
    """
    История отпусков сотрудника.
    Хранит факты ухода в отпуск с датами и количеством дней.
    """
    __tablename__ = "vacation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(
        BigInteger,
        ForeignKey("staff_vacation.id", onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    days_count = Column(Integer, nullable=False)  # Количество дней отпуска (календарных)
    type = Column(VARCHAR(50), default='paid')  # Тип: paid, unpaid, migration_balance и т.д.
    created_at = Column(DateTime, default=datetime.datetime.now)
    comment = Column(Text, nullable=True)  # Комментарий (опционально)

    # Relationship
    staff = relationship("StaffVacation", backref="vacation_history")

    @classmethod
    async def get_by_staff_id(
            cls,
            staff_id: int,
            session: AsyncSession
    ) -> typing.Sequence['VacationHistory']:
        """Получить всю историю отпусков сотрудника, отсортированную по дате начала"""
        stmt = select(VacationHistory).where(
            VacationHistory.staff_id == staff_id
        ).order_by(VacationHistory.date_start)
        response = await session.execute(stmt)
        return response.scalars().all()

    @classmethod
    async def get_total_used_days(
            cls,
            staff_id: int,
            session: AsyncSession
    ) -> int:
        """Получить общее количество использованных дней отпуска"""
        stmt = select(func.coalesce(func.sum(VacationHistory.days_count), 0)).where(
            VacationHistory.staff_id == staff_id
        )
        result = await session.scalar(stmt)
        return int(result) if result else 0

    @classmethod
    async def create(
            cls,
            staff_id: int,
            date_start: datetime.date,
            date_end: datetime.date,
            days_count: int,
            vacation_type: str = 'paid',
            comment: str = None,
            session: AsyncSession = None
    ) -> 'VacationHistory':
        """Создать новую запись в истории отпусков"""
        vacation_record = VacationHistory(
            staff_id=staff_id,
            date_start=date_start,
            date_end=date_end,
            days_count=days_count,
            type=vacation_type,
            comment=comment
        )
        session.add(vacation_record)
        return vacation_record
